import heapq
import numpy as np
import matplotlib.pyplot as plt
from smart_crazyflie.lib.motion_controller import Position
from smart_crazyflie.lib.mapper.cell import Cell, CellState
from smart_crazyflie.lib.mapper import MapperAndLocaliser
import math
from smart_crazyflie.lib.obstacle_avoider import AVOID_DISTANCE, ROBOT_AVOID_DISTANCE
from smart_crazyflie.lib.common import FRONT_HEADING, ROBOT_SIZE

def decompose_vector(a, b):
        """
        Decomposes vector 'a' into components parallel and perpendicular to vector 'b'.
        """
        # 1. Normalize the direction vector b to a unit vector
        b_unit = b / np.linalg.norm(b)
        
        # 2. Calculate the scalar projection (magnitude along b)
        scalar_projection = np.dot(a, b_unit)
        
        # 3. Calculate the parallel vector component
        a_parallel = scalar_projection * b_unit
        
        # 4. Calculate the perpendicular vector component
        a_perpendicular = a - a_parallel
        
        return a_parallel, a_perpendicular

def check_scalar_direction(parallel_vec, target_dir_vec):
    # Multiply the numbers to find the relative sign
    product = np.dot(parallel_vec, target_dir_vec)
    
    return product > 0
   

class ForceFieldPathPlanner:
    def __init__(self, mapper: MapperAndLocaliser):
        self.mapper = mapper
        self.goal_attraction_constant = 20
        self.explored_already_repulstion_constant = 4
        # this is what it can use to adjust motion
        self.min_awareness_distance = 0.20  # metres beyond the robot dimension
        self.min_awareness_cells = self.mapper.dist_to_i(self.min_awareness_distance) # metres beyond the robot dimension

   
    
    def repulsion_force_for_goal(self, repulsion_force, goal_force):
        toward, away = decompose_vector(repulsion_force, goal_force)

        if check_scalar_direction(toward, goal_force):
            return toward +away
        
        return away 

    def current_force(self, goal):
        if not self.mapper.motion.current_rot.is_valid():
            return None, None

        # goal is positive force
        # obstacles are negative forces
        # as vector

        obstacles = self.mapper.obstacles
        me_cell = self.mapper.me_cell
        close_obstacles = []
        for obstacle in obstacles:
            cells_away = math.hypot(
                    obstacle[0] - me_cell.x, obstacle[1] - me_cell.y
                )

            cell = self.mapper.map_as_matrix[obstacle[0]][obstacle[1]]
            if cells_away < self.min_awareness_cells and cell.occupied_status == CellState.OBSTACLE:
                if cell.override != CellState.MISSION_OBJECTIVE:
                    cell.override = CellState.CLOSE_OBSTACLE
                close_obstacles.append(obstacle)
            elif cell.override == CellState.CLOSE_OBSTACLE:
                cell.override = None
        # print(f"{len(obstacles)} total obstacles, {len(close_obstacles)} are close by")

        attractive_forces = [
            self.calculate_force_on(goal, True)
            ]
        repulsive_forces = [
        #    self.calculate_force_on(self.mapper.cell_to_pos(obstacle)) 
        #    for obstacle in close_obstacles
        # ]  + [
        #     self.calculate_force_on(self.mapper.cell_to_pos(already_been_cell), False, True) 
        #    for already_been_cell in self.mapper.travelled_path
        ]
        forces = repulsive_forces + attractive_forces
        
        if len(forces) == 0:
            return None, None
        
        resultant_force = np.sum(forces, axis=0)

        print("sum of forces")
        # print(resultant_force)

        if resultant_force[0] == 0:
            return None, None

        robot_heading = self.mapper.motion.current_rot.yaw % 360
        raw_bearing = math.degrees(np.arctan(resultant_force[1]/ resultant_force[0])) % 360
        bearing = raw_bearing - robot_heading
        bearing = bearing % 360
        if resultant_force[0] < 0:
            bearing = bearing + 180

        # print(round(raw_bearing), round(bearing))
        cells_force = self.mapper.cells_hit_by_range_beam(self.mapper.motion.current_pos, bearing, 0.6)
        for row_i, row in enumerate(self.mapper.map_as_matrix):
            for col_i, cell in enumerate(row):
                if (row_i, col_i) in cells_force:
                    cell.override = CellState.MOTION_FORCE
                elif cell.override == CellState.MOTION_FORCE:
                    cell.override = None

        return resultant_force, bearing

    def calculate_force_on(self, influencing_obj_pos: Position, attractive=False, historical=False):
        me_pos = self.mapper.motion.current_pos
        if not me_pos:
            return np.array([0.0 for x in influencing_obj_pos])

        diff = influencing_obj_pos.list - me_pos.list
        diff_magnitude = np.linalg.norm(diff)

        if attractive:
            # the goal magnitude doesn't need to increase, 
            # it just needs to influence enough for roaming to not be random
            # force_magnitude = diff_magnitude * self.goal_attraction_constant
            force_magnitude =  self.goal_attraction_constant
        elif historical:
             force_magnitude = -1 * self.explored_already_repulstion_constant
        else:
            # the object cannot be a negative distance away
            diff_magnitude = max(diff_magnitude - ROBOT_SIZE, 10 ** -5)
            force_magnitude = -1 * (
                max((1/diff_magnitude) - (1 / self.min_awareness_distance), 0)
            )
            force_magnitude = min(force_magnitude, 100)

        force = diff * force_magnitude / diff_magnitude
        return force
