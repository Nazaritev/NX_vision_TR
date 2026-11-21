"""Runtime contract for the formal unseeded localization node."""

import os
from pathlib import Path
import signal
import subprocess
import time

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from diagnostic_msgs.msg import DiagnosticArray
import rclpy
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import TransformStamped


def _spin_until(node, predicate, timeout_sec):
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        if predicate():
            return True
    return False


def test_unseeded_node_rejects_competing_map_odom(tmp_path):
    os.environ['RMW_IMPLEMENTATION'] = 'rmw_cyclonedds_cpp'
    os.environ.pop('CYCLONEDDS_URI', None)
    os.environ['ROS_DOMAIN_ID'] = '218'
    os.environ['ROS_LOG_DIR'] = str(tmp_path / 'logs')
    (tmp_path / 'logs').mkdir()

    prefix = Path(get_package_prefix('rc_bbs_localization'))
    share = Path(get_package_share_directory('rc_bringup'))
    executable = prefix / 'lib' / 'rc_bbs_localization' / 'bbs_localizer'
    params = share / 'config' / 'reality' / 'rc_localization.yaml'
    map_file = share / 'map' / '1.pcd'
    process = subprocess.Popen(
        [
            str(executable), '--ros-args', '--params-file', str(params),
            '-p', f'map_file:={map_file}',
            '-p', f'metrics_file:={tmp_path / "metrics.csv"}',
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )

    rclpy.init()
    probe = rclpy.create_node('bbs_contract_probe')
    statuses = []
    status_subscription = probe.create_subscription(
        DiagnosticArray, '/bbs_localization/status', statuses.append, 10)
    qos = QoSProfile(
        depth=1,
        reliability=ReliabilityPolicy.RELIABLE,
        durability=DurabilityPolicy.TRANSIENT_LOCAL,
    )
    tf_publisher = probe.create_publisher(TFMessage, '/tf_static', qos)

    try:
        def localizer_visible():
            return any(
                name == 'bbs_localizer' and namespace == '/'
                for name, namespace in probe.get_node_names_and_namespaces()
            )

        assert _spin_until(probe, localizer_visible, 8.0), 'bbs_localizer did not start'
        subscriptions = probe.get_subscriber_names_and_types_by_node('bbs_localizer', '/')
        assert subscriptions is not None
        assert '/initialpose' not in {name for name, _ in subscriptions}

        transform = TransformStamped()
        transform.header.stamp = probe.get_clock().now().to_msg()
        transform.header.frame_id = 'map'
        transform.child_frame_id = 'odom'
        transform.transform.rotation.w = 1.0
        message = TFMessage(transforms=[transform])
        for _ in range(5):
            tf_publisher.publish(message)
            rclpy.spin_once(probe, timeout_sec=0.05)

        def conflict_reported():
            return any(
                status.name == 'bbs_localization'
                and status.level == status.ERROR
                and 'competing_map_odom_publisher' in status.message
                for array in statuses
                for status in array.status
            )

        assert _spin_until(probe, conflict_reported, 5.0)
        conflict = next(
            status
            for array in reversed(statuses)
            for status in array.status
            if 'competing_map_odom_publisher' in status.message
        )
        values = {item.key: item.value for item in conflict.values}
        assert values['pose_valid'] == '0'
        assert values['allow_initialpose'] == '0'
        assert status_subscription is not None
    finally:
        probe.destroy_node()
        rclpy.shutdown()
        process.send_signal(signal.SIGINT)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

