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
        self.last_packet:PoseStamped = None
        self.camera_position_from_dock = Position(0.2, 0, 0)

    # relative to map origin

    @property
    def offset_from_camera(self):
        if self.last_packet is None:
            return None

        time = self.last_packet.header.stamp
        self.node.logger.info(str(time))
        
        if time > self.motion.phase_handle.now + 5:
            return None

        return self.last_packet.pose.position

    @property
    def offset_from_dock(self):
        if self.offset_from_camera is None:
            return None

        return Position(*self.last_packet.pose.position) - self.camera_position_from_dock


    def course_correction(self):
        offset = self.offset_from_dock
        if not offset:
            return None

        offset_dist = np.linalg.norm(offset.list) 
        if offset_dist < 0.05:
            return None

        return self.motion.drive()

    def aruco_callback(self, msg: PoseStamped):
        self.last_packet = msg
        self.node.logger.info(str(msg.header))
        self.node.logger.info(str(self.last_packet))


        

        # self.mapper.update(CellState.ME, )

    def control_loop(self):
        self.phase_handle.control_loop()
