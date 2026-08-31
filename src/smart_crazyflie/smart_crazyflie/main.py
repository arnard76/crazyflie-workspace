"""
MSc in Computer Science Thesis
Crazyflie 2.1+ Drone Software Modules
"""

import json

from smart_crazyflie.lib.motion_controller import Position
import rclpy
from rclpy.node import Node
from smart_crazyflie.lib.motion_controller import MotionController
from smart_crazyflie.lib.phase_handler import PhaseManager
from smart_crazyflie.lib.obstacle_avoider import ObstacleAvoider
from smart_crazyflie.lib.auto_roamer import AutonomousRoamer
from smart_crazyflie.lib.mapper import MapperAndLocaliser
from smart_crazyflie.lib.red_detector import RedFinder
from smart_crazyflie.lib.locate_markers.measure_live_locations import locate_marker
import cv2
from smart_crazyflie.lib.common import ROBOT_SIZE
import numpy as np
from smart_crazyflie.lib.phase_handler import Phase

from crazyflie_py import Crazyswarm
from crazyflie_py.crazyflie import Crazyflie
from smart_crazyflie.lib.aruco_dock_assistant import MarkerLocaliser

dock = Position(1, 0, 0)

class SmartCrazyflie(Node):
    def __init__(self, swarm):
        super().__init__("smart_crazyflie")
        self.logger = self.get_logger()
        self.logger.info("Goal: ????")

        self.global_phase_handle = PhaseManager(self)
        self.cf: Crazyflie = swarm.allcfs.crazyflies[0]
        self.motion = MotionController(self, self.cf, self.global_phase_handle)

        self.avoider = ObstacleAvoider(self, self.motion)
        self.mapper = MapperAndLocaliser(self, self.motion)
        self.auto_roamer = AutonomousRoamer(self, self.mapper, self.motion)
        # self.auto_roamer.start_roaming()
        self.marker_localiser = MarkerLocaliser(self, self.mapper, self.motion)
        # self.rest_api =

        self.moving_home = False
        self.going_for_red = False

        self.timer = self.create_timer(0.1, self.control_loop)
        self.start_time = self.global_phase_handle.now

        self.TIMEOUT = 10 * 60 - 20  # 10 minutes - 20s for safety

        self.logger.info("Working towards goal...")

        self.GO_HOME_TIMEOUT = 5  # s
        self.global_phase_handle.add_phases([
            Phase("takeoff", lambda p: self.motion.takeoff(p, 2.0, 0.45)),
            Phase("mapping", lambda p: self.motion.go_to(p, 2.0, 0.5, 0.0, 0.5, 0.0,))]
        )

    def control_loop(self):
        if self.global_phase_handle.now - self.start_time > self.TIMEOUT:
            raise Exception("Node is FINISHED! Auto timeout")

        # TODO: shift this state to be "battery low" or "mapping complete"
        need_to_move_home = (
            self.global_phase_handle.now - self.start_time > self.GO_HOME_TIMEOUT
        )

        if need_to_move_home:
            if not self.moving_home:
                # TODO: turn camera on, start tracking, do once whole thing is moved to UGV

                # TODO: the moving home also requires autonomous
                # self.auto_roamer.start_moving_to_home()

                self.global_phase_handle.add_phases(
                    [
                        Phase(
                            "fly above dock", lambda p: self.motion.go_to(p, 5.0, dock.x, dock.y, dock.z + 1, 0)
                        ),
                        Phase("lower into dock", lambda p: self.motion.go_to(p, 5.0, dock.x, dock.y, dock.z, 0)),
                        Phase("land in dock", lambda p: self.motion.land(p, 0.5)),
                    ]
                )
            self.moving_home = True

        # self.logger.info(json.dumps(self.cf.status))
        if not self.marker_localiser:
            if not self.moving_home:
                # TODO: need to reset for correct historical repulsion
                # but also it would be good to store the entire history
                # currently it is being stored in the grid though so no worries!
                self.mapper.travelled_path = []
                self.auto_roamer.current_goal = 0
                if not self.auto_roamer:
                    self.auto_roamer = AutonomousRoamer(self, self.mapper, self.motion)
                self.auto_roamer.start_moving_to_home()
                self.mapper.save_map()
                self.moving_home = True

            dist_away_from_goal = np.linalg.norm(
                self.motion.current_pos.list - self.mapper.ROBOT_START.list
            )

            if dist_away_from_goal < 0.5:
                raise Exception("Reached home")

            self.global_phase_handle.control_loop()

        # elif self.marker_localiser.last_packet:
        #     self.logger.info('red found')
        #     self.destroy_subscription(self.red_finder.img_sub)
        #     self.red_finder = None
        # elif not self.red_finder.last_packet and self.red_finder.red_detected:
        #     self.logger.info('red detected, and roaming? ', self.going_for_red)
        #     if not self.going_for_red and self.mapper.goal_cell:
        #         self.going_for_red = True
        #         self.auto_roamer.stop_roaming()
        #         goal = self.mapper.goal_cell
        #         self.auto_roamer.start_moving_to_goal_red(self.mapper.cell_to_pos(goal))

        #     self.global_phase_handle.control_loop()
        else:

            self.global_phase_handle.control_loop()


def main():
    swarm = Crazyswarm()
    node = SmartCrazyflie(swarm)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt as e:
        node.logger.info("User Stopped Program")
        swarm.allcfs.emergency()
    except Exception as e:
        node.logger.info(e)
        node.logger.info("Error Stopped Program")
        swarm.allcfs.emergency()
    finally:
        node.mapper.save_map()
        node.logger.info(
            f"Red Object Found at {node.mapper.goal_cell and node.mapper.cell_to_pos(node.mapper.goal_cell)} | Robot is at {node.motion.current_pos}"
        )

        cv2.destroyAllWindows()
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass


if __name__ == "__main__":
    main()
