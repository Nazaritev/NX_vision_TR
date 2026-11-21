"""Standalone PCD localization: MID360 -> FAST-LIO -> BBS/GICP -> RViz.

Edit config/reality/rc_localization_launch.yaml for process switches and map path.
Edit config/reality/rc_localization.yaml for localization tuning.
Start with: ros2 launch rc_bringup rc_localization.launch.py
"""

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import EmitEvent, LogInfo, RegisterEventHandler, SetEnvironmentVariable
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = Path(get_package_share_directory('rc_bringup'))
    config_dir = share / 'config' / 'reality'
    settings_path = config_dir / 'rc_localization_launch.yaml'

    with settings_path.open(encoding='utf-8') as stream:
        settings = yaml.safe_load(stream)

    mode = settings['input_mode']
    if mode not in ('live', 'external'):
        raise ValueError('input_mode must be live or external')

    for key in ('use_sim_time', 'start_robot_state_publisher', 'start_rviz'):
        if type(settings[key]) is not bool:
            raise ValueError(f'{key} must be a YAML boolean')

    configured_map = Path(str(settings['map_file'])).expanduser()
    map_file = (configured_map if configured_map.is_absolute() else share / 'map' / configured_map).resolve()
    if not map_file.is_file():
        raise FileNotFoundError(f'Localization PCD is missing: {map_file}')

    dds_profile = settings['dds_profile']
    if dds_profile not in ('local', 'system'):
        raise ValueError('dds_profile must be local or system')
    rviz_view = settings.get('rviz_view', 'map')
    if rviz_view not in ('map', 'odom'):
        raise ValueError('rviz_view must be map or odom')

    fast_lio_config = Path(str(settings.get('fast_lio_config', 'rc_localization_fast_lio.yaml')))
    if not fast_lio_config.is_absolute():
        fast_lio_config = config_dir / fast_lio_config
    if mode == 'live' and not fast_lio_config.is_file():
        raise FileNotFoundError(f'FAST-LIO configuration is missing: {fast_lio_config}')

    clock = {'use_sim_time': settings['use_sim_time']}
    actions = [LogInfo(msg=(
        f'PCD localization: {map_file}; input_mode={mode}. '
        'Automatic localization starts without an initial position and publishes no /initialpose. '
        'The production localizer also ignores RViz 2D Pose Estimate input.'
    ))]

    actions.append(SetEnvironmentVariable('ROS_DOMAIN_ID', str(settings['ros_domain_id'])))
    if dds_profile == 'local':
        actions.extend([
            SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
            SetEnvironmentVariable(
                'CYCLONEDDS_URI',
                (config_dir / 'rc_localization_dds.xml').as_uri(),
            ),
        ])

    if settings['start_robot_state_publisher']:
        actions.append(Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='bbs_robot_state_publisher',
            output='screen',
            parameters=[clock, {
                'robot_description': ParameterValue(
                    Command(['xacro ', str(share / 'urdf' / 'reality' / 'rc_localization_model.xacro')]),
                    value_type=str,
                ),
            }],
        ))

    if mode == 'live':
        actions.append(Node(
            package='livox_ros_driver2',
            executable='livox_ros_driver2_node',
            name='bbs_livox',
            output='screen',
            parameters=[clock, {
                'xfer_format': 1,
                'multi_topic': 0,
                'data_src': 0,
                'publish_freq': 40.0,
                'output_data_type': 0,
                'frame_id': 'livox_frame',
                'user_config_path': str(config_dir / 'rc_localization_mid360.json'),
            }],
        ))

        actions.append(Node(
            package='fast_lio',
            executable='fastlio_mapping',
            name='bbs_fast_lio',
            output='screen',
            parameters=[str(fast_lio_config), clock, {
                'map_file_path': '',
                'pcd_save.pcd_save_en': False,
                'publish.scan_publish_en': True,
                'publish.scan_bodyframe_pub_en': True,
            }],
        ))

    localizer = Node(
        package='rc_bbs_localization',
        executable='bbs_localizer',
        name='bbs_localizer',
        output='screen',
        parameters=[str(config_dir / 'rc_localization.yaml'), clock, {
            'map_file': str(map_file),
        }],
    )
    actions.extend([
        RegisterEventHandler(OnProcessExit(
            target_action=localizer,
            on_exit=[EmitEvent(event=Shutdown(reason='bbs_localizer exited'))],
        )),
        localizer,
    ])

    if settings['start_rviz']:
        actions.append(Node(
            package='rviz2',
            executable='rviz2',
            name='bbs_localization_rviz',
            output='screen',
            arguments=['-d', str(share / 'rviz' / (
                'rc_localization_odom.rviz' if rviz_view == 'odom' else 'rc_localization.rviz'))],
            parameters=[clock],
        ))

    return LaunchDescription(actions)
