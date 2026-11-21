cmake_minimum_required(VERSION 3.10)
project(rc_bringup)

if(CMAKE_EXPORT_COMPILE_COMMANDS)
  set(CMAKE_EXPORT_COMPILE_COMMANDS ${CMAKE_EXPORT_COMPILE_COMMANDS})
endif()

find_package(ament_cmake_auto REQUIRED)

install(PROGRAMS
  scripts/amcl_pose_counter.py
  scripts/goal_distance_stop.py
  scripts/wait_for_localization.py
  scripts/gripper_pointcloud_filter.py
  docs/rc_bbs_validation/tools/real_acceptance.py
  docs/rc_bbs_validation/tools/audit_input_bag.py
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  find_package(ament_cmake_pytest REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
  ament_add_pytest_test(test_gripper_pointcloud_filter
    test/test_gripper_pointcloud_filter.py
    TIMEOUT 60
  )
  ament_add_pytest_test(test_gripper_filter_ros
    test/test_gripper_filter_ros.py
    TIMEOUT 90
  )
  ament_add_pytest_test(test_real_acceptance
    docs/rc_bbs_validation/tools/test_real_acceptance.py
    TIMEOUT 60
  )
  ament_add_pytest_test(test_audit_input_bag
    docs/rc_bbs_validation/tools/test_audit_input_bag.py
    TIMEOUT 30
  )
  ament_add_pytest_test(test_rc_localization_launch
    test/test_rc_localization_launch.py
    TIMEOUT 30
  )
endif()

ament_auto_package(
  INSTALL_TO_SHARE
  behavior_trees
  config
  launch
  map
  urdf
  meshes
  rviz
  world
)
