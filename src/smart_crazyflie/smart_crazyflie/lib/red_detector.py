import cv2
import numpy as np
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from cv_bridge import CvBridge
from rclpy.node import Node
from smart_crazyflie.lib.common import NAMESPACE
from smart_crazyflie.lib.motion_controller import MotionController
from smart_crazyflie.lib.phase_handler import PhaseManager
from smart_crazyflie.lib.mapper import MapperAndLocaliser
import os
from smart_crazyflie.lib.mapper.cell import Cell, CellState

# HSV thresholds for red — use your Investigation C values
# Red wraps around hue 0/180, so two ranges are needed
RED_LOW1  = np.array([0, 180, 100])
RED_HIGH1 = np.array([10, 255, 255])
RED_LOW2  = np.array([170, 180, 100])
RED_HIGH2 = np.array([179, 255, 255])

# Minimum pixel count to count as a detection
# Use the value you established in Investigation C
MIN_PIXELS = 800
RED_FOUND_PIXELS = 9000

# TODO: verify! this value I guessed it mostly
CAMERA_FOV = 25 # degrees
# CAMERA_RES = [1080, 1920] # compressed = unknown image res


class RedFinder():
    STEP_TOWARDS_RED = 0.4 # mt

    def __init__(self, node: Node, mapper: MapperAndLocaliser, motion: MotionController):
        self.node = node
        self.motion = motion
        self.mapper = mapper
        self.bridge = CvBridge()
        topic = f'{NAMESPACE}/oakd/rgb/image_raw/compressed'
        self.img_sub = self.node.create_subscription(
            CompressedImage, topic, self.image_callback, 10)
        self.logger = self.node.get_logger()
        self.logger.info('Camera detector started')

        self.red_found = False
        self.red_detected = False
        self.red_count = 0
        self.red_bearing = 0


    def image_callback(self, msg):
        img = self.bridge.compressed_imgmsg_to_cv2(msg, 'bgr8')
        self.red_count, mask = self.detect_red_pixels(img)

        # PREVIEW IMG
        overlay = img.copy()
        overlay[mask > 0] = [0, 0, 255]
        cv2.putText(overlay, f'Red pixels: {self.red_count}', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        if self.red_count >= MIN_PIXELS:
            cv2.putText(overlay, 'DETECTED', (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            # self.logger.info(f'Red cube detected — {self.red_count} pixels')
            self.red_detected  = True

            h, w, c = img.shape
            x,y = self.locate_red_detection(mask)
            cv2.circle(overlay, (x, y), 5, (255, 255, 255), -1)
            cv2.putText(overlay, "centroid", (x - 25, y - 25),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            self.red_bearing  = self.calculate_bearing_for_location(x,y, w,h)
            cv2.putText(overlay, f"{self.red_bearing:.0f}deg from straight ahead",  (10,90),cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)



            if not self.red_found:
                if self.motion.current_pos.is_valid():
                    possible_cells = self.mapper.cells_hit_by_range_beam(self.motion.current_pos, self.red_bearing, 2.0)
                    
                    for cell_i in self.mapper.possible_goals_cells:
                        cell:Cell = self.mapper.cell_at(cell_i)
                        cell.update_probability_mission_objective(cell_i in possible_cells)

                    self.mapper.possible_goals_cells += possible_cells

                    largest_score = 0
                    best_cell = None
                    for cell_i in self.mapper.possible_goals_cells:
                        cell = self.mapper.cell_at(cell_i)
                        if cell.override == CellState.MISSION_OBJECTIVE:
                            cell.override = None

                        if cell.mission_objective_likeliness_score > largest_score:
                            best_cell = cell_i
                            largest_score = cell.mission_objective_likeliness_score

                    if best_cell:                          
                        self.mapper.cell_at(best_cell).override = CellState.MISSION_OBJECTIVE
                        self.mapper.goal_cell = best_cell

                b = self.red_bearing
                direction = -1 if b < 0 else 1 
                rotate_to_red = lambda: self.motion.rotate_for(b, self.motion.DEFAULT_TURN_SPEED * direction)
                drive_to_red = lambda: self.motion.drive_for(self.STEP_TOWARDS_RED)
                name = f"RED: Adjusting bearing {self.red_bearing:.1f} to red"
                # if not self.motion.phase_handle.current_phase or  "RED" not  in self.motion.phase_handle.current_phase['name']:
                #     self.motion.phase_handle.add_phases([{"actions": rotate_to_red, "name": name},
                #                                         {"actions": drive_to_red, "name": f"RED: Driving {self.STEP_TOWARDS_RED}m to red"}, {"name": "Empty phase", "actions": lambda: None}])
                
                #     self.motion.phase_handle.skip_to_phase_by_index(len(self.motion.phase_handle.phases)-3)
                
            # print("num possible cells", len(self.mapper.possible_goals_cells))
            if self.red_count > RED_FOUND_PIXELS:
                if not self.red_found:
                    self.red_found = True
                    timestamp = self.node.get_clock().now().nanoseconds / 1e9

                    if self.mapper.goal_cell and self.motion.current_pos.is_valid():
                        self.logger.info(f"Red Object Found at {self.mapper.cell_to_pos(self.mapper.goal_cell)} | Robot is at {self.motion.current_pos}")
                    elif self.mapper.goal_cell: 
                        self.logger.info(f"Red Object Found at {self.mapper.cell_to_pos(self.mapper.goal_cell)}")
                    elif self.motion.current_pos.is_valid():
                        self.logger.info(f"Red Object Found | Robot at {self.motion.current_pos}")
                    else:
                        self.logger.info(f"Red Object Found but robot has no idea where it is or the red object is ._.")

                    snap_path = os.path.join("mission", "red-box", f'image-{timestamp}.png')
                    snap_path_2 = os.path.join("mission", "red-box", f'overlay-{timestamp}.png')

                    cv2.imwrite(snap_path, img)
                    cv2.imwrite(snap_path_2, overlay)

            else:
                self.red_found = False
                
        else:
            self.red_found = False
            self.red_detected = False
        
        
        cv2.imshow('Detection', overlay)
        cv2.waitKey(1)


    def calculate_bearing_for_location(self, x, y, width, height):
        """
        Calculates the physical bearing towards a pixel location
        """
        offset_from_centre = width / 2 - x
        ratio = offset_from_centre /( width /2 )
        bearing = ratio * 12.5
        return bearing

    
    def locate_red_detection(self,  mask) -> tuple[int, int]:
        """
        Finds the image location (x, y) in pixels, of the red object in frame. 
        """
        # calculate moments for each contour
        M = cv2.moments(mask)

        # calculate x,y coordinate of center
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        
        return cX, cY


    def detect_red_pixels(self, img):
        hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, RED_LOW1, RED_HIGH1),
            cv2.inRange(hsv, RED_LOW2, RED_HIGH2)
        )
        pixels = cv2.countNonZero(mask)
        
        return pixels, mask


    def control_loop(self):
        self.phase_handle.control_loop()


