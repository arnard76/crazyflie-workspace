import json

import cv2
import numpy as np
from smart_crazyflie.lib.motion_controller import Position
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge
from rclpy.node import Node
from smart_crazyflie.lib.common import NAMESPACE
from smart_crazyflie.lib.motion_controller import MotionController
from smart_crazyflie.lib.phase_handler import PhaseManager
from smart_crazyflie.lib.mapper import MapperAndLocaliser
import os
from smart_crazyflie.lib.mapper.cell import Cell, CellState
from geometry_msgs.msg import PoseStamped

# TODO: verify! this value I guessed it mostly
CAMERA_FOV = 25  # degrees
# CAMERA_RES = [1080, 1920] # compressed = unknown image res


class MarkerLocaliser:
    def __init__(
        self, node: Node, mapper: MapperAndLocaliser, motion: MotionController
    ):
        self.node = node
        self.motion = motion
        self.mapper = mapper
        topic = f"aruco"
        self.aruco_sub = self.node.create_subscription(
            PoseStamped, topic, self.aruco_callback, 10
        )
        self.last_packet = None
        self.camera_position = self.mapper.ROBOT_START

    # relative to map origin

    def aruco_callback(self, msg: PoseStamped):
        self.last_packet = {"pose": msg.pose, "header": msg.header}
        self.node.logger.info(str(msg.header))
        self.node.logger.info(str(self.last_packet))

        # self.mapper.update(CellState.ME, )

    def control_loop(self):
        self.phase_handle.control_loop()
