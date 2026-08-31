from typing import Literal, Self

from sympy import Quaternion
from smart_crazyflie.lib.phase_handler import Phase
from rclpy.node import Node
import math
from geometry_msgs.msg import Twist
from smart_crazyflie.lib.common import NAMESPACE
from smart_crazyflie.lib.phase_handler import PhaseManager
from nav_msgs.msg import Odometry
import numpy as np
from crazyflie_py.crazyflie import Crazyflie


class Orientation:
    pitch: float  # degrees
    roll: float  # degrees
    yaw: float  # degrees

    def __init__(self, pitch=float("nan"), roll=float("nan"), yaw=float("nan")):
        self.pitch = pitch
        self.roll = roll
        self.yaw = yaw

    def __str__(self):
        val = ""
        if self.pitch is not None:
            val += f"Pitch: {self.pitch:.1f}°,"
        if self.roll is not None:
            val += f"Roll: {self.roll:.1f}°,"
        if self.yaw is not None:
            val += f"Yaw: {self.yaw:.1f}°,"
        return val

    @property
    def list(self):
        return np.array([self.pitch, self.roll, self.yaw])

    def is_valid(self):
        return not any(math.isnan(x) for x in self.list)


class Position:
    x: float  # m
    y: float  # m
    z: float  # m
    units: Literal["m", "index"]

    def __init__(self, x=float("nan"), y=float("nan"), z=float("nan")):
        self.x = x
        self.y = y
        self.z = z
        self.units = "m"

    def is_valid(self):
        return not any(math.isnan(x) for x in self.list)

    def __str__(self):
        return f"({self.x:.1f}, {self.y:.1f}, {self.z:.1f}) {self.units}"

    @property
    def list(self):
        return np.array([self.x, self.y, self.z])

    def __add__(self, other):
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other):
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)


class MotionController:
    DEFAULT_FORWARD_SPEED = 0.20  # m/s — keep low on physical robot
    DEFAULT_TURN_SPEED = math.degrees(0.5)

    def __init__(self, node: Node, cf: Crazyflie, global_phase_handle: PhaseManager):
        self.node = node
        self.phase_handle = global_phase_handle
        self.cf = cf
        self.vel_publisher = self.node.create_publisher(
            Twist, f"{NAMESPACE}/cmd_vel", 10
        )

        self.node.create_subscription(
            Odometry, f"{NAMESPACE}/odom", self.odom_callback, 10
        )
        self.current_pos = Position()
        self.current_rot = Orientation()

    def odom_callback(self, msg):
        self.current_pos.x = msg.pose.pose.position.x
        self.current_pos.y = msg.pose.pose.position.x
        self.current_pos.z = msg.pose.pose.position.z

        # Convert quaternion to yaw in degrees
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_rot.yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

    def go_to(self, phase:Phase, duration_in_s, x, y, z, yaw):
        curr_phase = self.phase_handle.current_phase

        if not curr_phase or curr_phase is not phase:
            return

        self.cf.goTo([float(x), float(y), float(z)], float(yaw), float(duration_in_s))
        phase.end_time = self.phase_handle.now + duration_in_s

    def takeoff(self, phase:Phase, duration_in_s, height):
        curr_phase = self.phase_handle.current_phase

        if not curr_phase or curr_phase is not phase:
            return

        self.cf.takeoff(targetHeight=height, duration=duration_in_s)
        phase.end_time = self.phase_handle.now + duration_in_s

    def land(self, phase: Phase, duration_in_s):
        curr_phase = self.phase_handle.current_phase

        if not curr_phase or curr_phase is not phase:
            return

        self.cf.notifySetpointsStop()
        self.cf.land(0.04, duration_in_s)
        phase.end_time = self.phase_handle.now + duration_in_s

    # def drive_uav(self):
    #     t = timeHelper.time() - start_time

    #     pos = np.array([0.0, 0.0, 1.0])
    #     vel = np.array([0.0, 0.0, 0.0])
    #     acc = np.array([0.0, 0.0, 0.0])
    #     yaw = 0.0
    #     omega = np.array([0.0, 0.0, 0.0]) # Angular velocity

    #     # Construct identity quaternion for orientation
    #     quat = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)

    #     # Stream the full state command to the firmware
    #     self.cf.cmdFullState(pos, vel, acc, yaw, omega, quat)

    def drive(self, linear, angular):
        """Publish a Twist command. Call with (0, 0) to stop."""
        msg = Twist()
        msg.linear.x = float(linear)
        msg.angular.z = float(angular)
        self.vel_publisher.publish(msg)

    # angles in degrees
    def rotate_for(self, angle, with_angular_speed=DEFAULT_TURN_SPEED):
        phase = self.phase_handle.current_phase

        if not phase:
            return

        now = self.phase_handle.now
        elapsed = now - phase.start_time
        if elapsed < abs(angle / with_angular_speed):
            self.drive(0.0, math.radians(with_angular_speed))
        else:
            self.stop()
            print(f"Final rotation: {self.current_rot}")
            self.phase_handle.start_next_phase()
            return True

    def drive_for(self, distance, with_speed=DEFAULT_FORWARD_SPEED):
        phase = self.phase_handle.current_phase

        if not phase:
            return

        now = self.phase_handle.now
        elapsed = now - phase.start_time

        if elapsed < distance / with_speed:
            self.drive(with_speed, 0.0)
        else:
            self.stop()
            print(
                f"Final position x: {self.current_x:.4f} m  y: {self.current_y:.4f} m"
            )
            self.phase_handle.start_next_phase()

            return True

    def stop(self):
        self.drive(0.0, 0.0)
