"""
Complete COMPSYS 732 - Mobile Autonomous Robotics - Mission: Red Box Finder & Arena Mapper
"""

import rclpy
from rclpy.node import Node
from smart_crazyflie.lib.motion_controller import MotionController
from smart_crazyflie.lib.phase_handler import PhaseManager
from smart_crazyflie.lib.obstacle_avoider import ObstacleAvoider
from smart_crazyflie.lib.auto_roamer import AutonomousRoamer
from smart_crazyflie.lib.mapper import MapperAndLocaliser
from smart_crazyflie.lib.red_detector import RedFinder
import cv2
from smart_crazyflie.lib.common import ROBOT_SIZE
import numpy as np

class SmartCrazyflie(Node):
    def __init__(self):
        super().__init__("smart_crazyflie")
        print("Goal: ????")

        self.global_phase_handle = PhaseManager(self)
        self.motion = MotionController(self, self.global_phase_handle)

        self.avoider = ObstacleAvoider(self, self.motion)
        self.mapper = MapperAndLocaliser(self, self.motion)
        self.auto_roamer = AutonomousRoamer(self, self.mapper, self.motion)
        self.auto_roamer.start_roaming()
        self.red_finder = RedFinder(self,self.mapper, self.motion)
        # self.rest_api = 
        
        self.moving_home = False
        self.going_for_red = False

        self.timer = self.create_timer(0.1, self.control_loop)
        self.start_time = self.global_phase_handle.now

        self.TIMEOUT = 10 * 60 - 20 # 10 minutes - 20s for safety

        self.get_logger().info("Working towards goal...")
    

    def control_loop(self):
        if self.global_phase_handle.now - self.start_time > self.TIMEOUT:
            raise Exception("Node is FINISHED! Auto timeout")

        if not self.red_finder:
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

            dist_away_from_goal = np.linalg.norm(self.motion.current_pos.list - self.mapper.ROBOT_START.list)
            
            if  dist_away_from_goal < 0.5:
                raise Exception("Reached home")

            self.global_phase_handle.control_loop()

        elif self.red_finder.red_found:
            print('red found')
            self.destroy_subscription(self.red_finder.img_sub)
            self.red_finder = None
        elif not self.red_finder.red_found and self.red_finder.red_detected:
            print('red detected, and roaming? ', self.going_for_red)
            if not self.going_for_red and self.mapper.goal_cell:
                self.going_for_red = True
                self.auto_roamer.stop_roaming()
                goal = self.mapper.goal_cell
                self.auto_roamer.start_moving_to_goal_red(self.mapper.cell_to_pos(goal))
            
            self.global_phase_handle.control_loop()
        else:
            self.global_phase_handle.control_loop()


def main(args=None):
    rclpy.init(args=args)
    node = SmartCrazyflie()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt as e:
        print("Ended program")
    finally:
        node.mapper.save_map()
        node.get_logger().info(f"Red Object Found at {node.mapper.goal_cell and node.mapper.cell_to_pos(node.mapper.goal_cell)} | Robot is at {node.motion.current_pos}")

        cv2.destroyAllWindows()
        node.destroy_node()
        try:
            rclpy.shutdown()
        except:
            pass

if __name__ == "__main__":
    main()
