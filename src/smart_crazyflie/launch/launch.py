import math
import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource


def static_frame(parent_frame: str, child_frame: str, xyz: list[float] = [0.0, 0.0, 0.0], ypr: list[float]=[0.0, 0.0, 0.0]):
    return LaunchDescription(
        [
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                arguments=[
                    "--x",
                    str(xyz[0]),
                    "--y",
                    str(xyz[1]),
                    "--z",
                    str(xyz[2]),
                    "--yaw",
                    str(ypr[0]),
                    "--pitch",
                    str(ypr[1]),
                    "--roll",
                    str(ypr[2]),
                    "--frame-id",
                    parent_frame,
                    "--child-frame-id",
                    child_frame,
                ],
            ),
        ]
    )


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

    rosbridge = Node(
        package="rosbridge_server",
        executable="rosbridge_websocket",
        name="rosbridge_websocket",
        output="screen",
        parameters=[{"address": "127.0.0.1"}, {"port": 9090}],
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
    static_frames = [static_frame("marker", "UAV"), static_frame("UGV", "UGV-camera", ypr=[0, math.pi/2, 0])]
    marker_frame = Node(
        package="smart_crazyflie",
        executable="marker_frame",
        name="marker_frame",
    )
    UGV_frame = static_frame("world", "UGV")  # just for now
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
            *moving_frames,
        ]
    )
