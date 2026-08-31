from geometry_msgs.msg import TransformStamped

import rclpy
from rclpy.node import Node

from smart_crazyflie.frames.util import quaternion_from_euler
from tf2_ros import TransformBroadcaster


import math

from geometry_msgs.msg import TransformStamped

import numpy as np

import rclpy
from rclpy.node import Node

from tf2_ros import TransformBroadcaster

from geometry_msgs.msg import PoseStamped


class MarkerFrame(Node):
    def __init__(self):
        super().__init__("tracking_UAV_marker_frame")

        # Declare and acquire `turtlename` parameter
        self.turtlename = (
            self.declare_parameter("turtlename", "turtle")
            .get_parameter_value()
            .string_value
        )

        # Initialize the transform broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)

        # Subscribe to a turtle{1}{2}/pose topic and call handle_turtle_pose
        # callback function on each message
        self.subscription = self.create_subscription(
            PoseStamped, f"aruco", self.handle_marker_pose, 10
        )
        self.subscription  # prevent unused variable warning

    def handle_marker_pose(self, msg:PoseStamped):
        t = TransformStamped()

        # Read message content and assign it to
        # corresponding tf variables
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = "UGV-camera"
        t.child_frame_id = "marker"

        # Turtle only exists in 2D, thus we get x and y translation
        # coordinates from the message and set the z coordinate to 0
        t.transform.translation.x = msg.pose.position.x
        t.transform.translation.y = msg.pose.position.y
        t.transform.translation.z = msg.pose.position.z

        # For the same reason, turtle can only rotate around one axis
        # and this why we set rotation in x and y to 0 and obtain
        # rotation in z axis from the message
        # t.transform.rotation = msg.pose.orientation

        # Send the transformation
        self.tf_broadcaster.sendTransform(t)


def main():
    rclpy.init()
    node = MarkerFrame()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()
