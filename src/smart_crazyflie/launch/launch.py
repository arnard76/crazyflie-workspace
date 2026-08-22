import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource



def static_frame(parent_frame: str, child_frame: str):
    return LaunchDescription([
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=[
                '--x', '0', '--y', '0', '--z', '0',
                '--yaw', '0', '--pitch', '0', '--roll',
                '0', '--frame-id', parent_frame, '--child-frame-id', child_frame]
        ),
    ])


def generate_launch_description():
    script = LaunchConfiguration("script", default="")
    backend = LaunchConfiguration("backend")

    script_launch_arg = DeclareLaunchArgument("script", default_value="")

    backend_launch_arg = DeclareLaunchArgument("backend", default_value="cpp")

    crazyflie = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(get_package_share_directory("crazyflie"), "launch"),
                "/launch.py",
            ]
        ),
        launch_arguments={
            "backend": backend,
        }.items(),
    )

    foxglove = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("foxglove_bridge"),
                "launch",
                "foxglove_bridge_launch.xml",
            )
        )
    )

    rosbridge = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("rosbridge_server"),
                "launch",
                "rosbridge_websocket_launch.xml",
            )
        )
    )

    smart_crazyflie_node = Node(
        package="smart_crazyflie",
        executable="main",
        name="smart_crazyflie_app",
        parameters=[
            {
                "use_sim_time": PythonExpression(["'", backend, "' == 'sim'"]),
            },
            {"hover_height": 0.3},
            {"incoming_twist_topic": "/cmd_vel"},
            {"robot_prefix": "/cf231"},
        ],
    )

    # frames
    static_frames = [static_frame('marker', 'UAV'), static_frame('UGV', 'UGV-camera')]
    marker_frame = Node(
        package="smart_crazyflie",
        executable="marker_frame",
        name="marker_frame",
    )
    UGV_frame = static_frame('UGV', 'world') # just for now
    moving_frames = [marker_frame, UGV_frame]

    return LaunchDescription(
        [
            script_launch_arg,
            backend_launch_arg,
            foxglove,
            rosbridge,
            crazyflie,
            smart_crazyflie_node,
            *static_frames,
            *moving_frames
        ]
    )
