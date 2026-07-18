"""
Don't allow the robot to hit anything or get stuck in a bad situation.
"""

from rclpy.node import Node
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
import math
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from smart_crazyflie.lib.common import NAMESPACE, FRONT_HEADING, ROBOT_SIZE
from smart_crazyflie.lib.motion_controller import MotionController

### OBSTACLE AVOIDANCE ###
ROBOT_AVOID_DISTANCE = 0.12  # metres - threshold to do AVOID action
AVOID_DISTANCE = ROBOT_SIZE + ROBOT_AVOID_DISTANCE  # metres
FRONT_ARC_DEG = 35  # degrees either side of forward to check


class ObstacleAvoider:
    def __init__(self, node: Node, motion: MotionController):
        self.node = node
        self.motion = motion
        # self.node.create_subscription(Odometry, f"{NAMESPACE}/odom", self.odom_callback, 10)

        self.scan_sub = self.node.create_subscription(
            LaserScan, f"{NAMESPACE}/scan", self.scan_callback, 10
        )
        self.logger = self.node.get_logger()

        self.phase_handle = self.motion.phase_handle

    def scan_callback(self, msg):
        inc = msg.angle_increment
        arc_r = math.radians(FRONT_ARC_DEG)
        side_r = math.radians(FRONT_ARC_DEG)
        front_rad = math.radians(FRONT_HEADING)
        front_index = int(round((front_rad - msg.angle_min) / inc))
        # front_i = int(round(-msg.angle_min / inc))
        half_a = int(round(arc_r / inc))
        side_a = int(round(side_r / inc))
        n = len(msg.ranges)

        def arc_min(lo, hi):
            lo = max(0, lo)
            hi = min(n - 1, hi)
            vals = [
                r for r in msg.ranges[lo : hi + 1] if msg.range_min < r < msg.range_max
            ]
            return min(vals) if vals else float("inf")

        self.nearest_front = arc_min(front_index - half_a, front_index + half_a)
        self.nearest_left = arc_min(front_index + half_a, front_index + side_a)
        self.nearest_right = arc_min(front_index - side_a, front_index - half_a)

        # OBSTACLE AVOIDANCE
        # print(
        #     f"left={self.nearest_left:.2f}m | front={self.nearest_front:.2f}m | right={self.nearest_right:.2f}m"
        # )

        phase = self.phase_handle.current_phase
        if (
            phase
            and "OA" not in phase["name"]
            and "rotate" not in phase["name"].lower()
            and self.nearest_front < AVOID_DISTANCE
        ):
            self.phase_handle.add_phase(
                {"name": "OA: Stop to avoid crash", "actions": lambda: None}
            )
            self.phase_handle.start_next_phase()
            phase = self.phase_handle.current_phase

    # def control_loop(self):
    #     self.phase_handle.control_loop()
