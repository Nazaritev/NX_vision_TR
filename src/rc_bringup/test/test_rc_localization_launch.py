"""Offline contract for the standalone, unseeded localization launch."""

import importlib.util
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
import yaml


SHARE = Path(get_package_share_directory("rc_bringup"))
ENTRY = SHARE / "launch" / "rc_localization.launch.py"
SPEC = importlib.util.spec_from_file_location("rc_localization_launch", ENTRY)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_formal_launch_uses_portable_private_inputs():
    settings_path = SHARE / "config" / "reality" / "rc_localization_launch.yaml"
    settings = yaml.safe_load(settings_path.read_text(encoding="utf-8"))
    localization = yaml.safe_load(
        (SHARE / "config" / "reality" / "rc_localization.yaml").read_text(encoding="utf-8")
    )["bbs_localizer"]["ros__parameters"]

    assert settings["input_mode"] == "live"
    map_path = Path(settings["map_file"])
    fast_lio_path = Path(settings["fast_lio_config"])
    assert not map_path.is_absolute()
    assert not fast_lio_path.is_absolute()
    assert (SHARE / "map" / map_path).is_file()
    assert (SHARE / "config" / "reality" / fast_lio_path).is_file()
    assert (SHARE / "config" / "reality" / "rc_localization_mid360.json").is_file()
    assert (SHARE / "urdf" / "reality" / "rc_localization_model.xacro").is_file()
    assert localization["allow_initialpose"] is False

    rviz = yaml.safe_load(
        (SHARE / "rviz" / "rc_localization.rviz").read_text(encoding="utf-8")
    )
    tools = rviz["Visualization Manager"]["Tools"]
    assert all(tool["Class"] != "rviz_default_plugins/SetInitialPose" for tool in tools)
    assert all(
        tool.get("Topic", {}).get("Value") != "/initialpose"
        for tool in tools
    )

    launch_source = ENTRY.read_text(encoding="utf-8")
    assert "rc_localization_model.xacro" in launch_source
    assert "rc_localization_mid360.json" in launch_source
    assert "fast_lio_config" in launch_source

    description = MODULE.generate_launch_description()
    assert description is not None
