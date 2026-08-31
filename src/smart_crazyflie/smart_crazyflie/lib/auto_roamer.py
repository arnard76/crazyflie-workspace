"""
Auto-roaming!

It is an automatic way of exploring an area.

- in danger, should return to safe spot
- low battery, should return to safe spot
- the area cannot be explored anymore, return to safe spot
- actually includes a way to move to safe spot
"""

from smart_crazyflie.lib.mapper import MapperAndLocaliser
from smart_crazyflie.lib.motion_controller import MotionController, Position
from rclpy.node import Node
import random
import math
import numpy as np
from smart_crazyflie.lib.path_plan.force_field_path_planner import ForceFieldPathPlanner
from smart_crazyflie.lib.common import ROBOT_SIZE
from smart_crazyflie.lib.phase_handler import Phase


direction = 1
class AutonomousRoamer:
    REPLAN_ROUTE_INTERVAl = 4  # every X seconds
    disabled = True

    def __init__(
        self, node: Node, mapper: MapperAndLocaliser, motion: MotionController
    ) -> None:
        self.mapper = mapper
        self.safe_spot = self.mapper.ROBOT_START
        self.motion = motion

        self.node = node
        self.current_goal = 0
        # self.motion.phase_handle.add_phase(Phase("roam towards unknown areas", self.path_towards_unknown_area))
        self.planner = ForceFieldPathPlanner(self.mapper)

        self.goals = [
            Position(self.mapper.ROBOT_START.x + direction * 3, self.mapper.ROBOT_START.y, 0),
            Position(self.mapper.ROBOT_START.x + direction * 3, self.mapper.ROBOT_START.y - direction * 3.5, 0) ,
            Position(self.mapper.ROBOT_START.x + direction * 1, self.mapper.ROBOT_START.y - direction * 3.5, 0)
        ]

    def start_moving_to_home(self):
        return self.start_moving_to_goal(self.current_goal)

    def start_moving_to_goal(self, goal):
        self.timer = self.node.create_timer(
            self.REPLAN_ROUTE_INTERVAl, self.path_towards_safe_spot
        )

    def start_moving_to_goal_red(self, goal):
        self.timer = self.node.create_timer(
            self.REPLAN_ROUTE_INTERVAl, lambda: self.move_to_force(goal)
        )

    def start_roaming(self):
        self.timer = self.node.create_timer(
            self.REPLAN_ROUTE_INTERVAl, self.move_to_unknown_area
        )

    def stop_roaming(self):
        if not self.timer:
            return

        self.timer.cancel()
        self.timer = None

    def move_to_force(self, goal):
        force, bearing = self.planner.current_force(goal)

        if force is None or bearing is None:
            return

        bearing = bearing % 360
        if bearing > 180:
            bearing = bearing - 360
        elif bearing < -180:
            bearing = bearing + 360

        print("rotating", np.round(bearing, 1))
        phases = [
            Phase(
                "Rotate towards force",
                lambda: self.motion.rotate_for(bearing),
            ),
             Phase(
                "force move",
                lambda: self.motion.drive_for(
                    self.motion.DEFAULT_FORWARD_SPEED * self.REPLAN_ROUTE_INTERVAl,
                    self.motion.DEFAULT_FORWARD_SPEED,
                ),
             ),
        ]

        if not self.disabled:
            self.motion.phase_handle.add_phases(phases)
            self.motion.phase_handle.skip_to_phase(phases[0].name)

    def plan_path_to(self, location: tuple[float]):
        current_pos = self.motion.current_pos
        if not current_pos.is_valid():
            return

        plan = self.planner.plan(
            self.mapper.cell_from_pos(current_pos).list, location
        )
        return plan

    def move_to_unknown_area(self):
        updated_plan = self.path_towards_unknown_area()

        if not updated_plan:
            return

        if not self.disabled:
            self.motion.phase_handle.add_phases(updated_plan)
            self.motion.phase_handle.skip_to_phase(updated_plan[0].name)

    def path_towards_unknown_area(self):
        # unknown area is the gray
        # but it needs to be reachable
        # meaning there needs to be a white spot
        # directly to gray
        # and white spot needs to be wide enough

        # find a patch of gray that isn't surrounded by black
        areas = self.mapper.reachable_unknown_areas()

        # if len(areas) == 0:
        #     return

        # print(areas)
        # area = areas[-1]
        # goal_pos = self.mapper.cell_to_pos(area)

        if not self.motion.current_pos:
            return

        dist_away_from_goal = np.linalg.norm(self.motion.current_pos.list - self.goals[self.current_goal].list)
        
        # print("right now:", self.motion.current_pos)
        # print("go to:", goals[self.current_goal])
        # print("difference", dist_away_from_goal)
        print("waypoint ", self.current_goal+1)
        
        if  dist_away_from_goal < ROBOT_SIZE + 0.2:
            self.current_goal += 1

        # middle_grid = np.array(self.mapper.GRID_SIZE_CELLS) /2
        # goal_pos = self.mapper.cell_to_pos(middle_grid)
        
        return self.move_to_force(self.goals[self.current_goal])

    def path_towards_safe_spot(self):
        # unknown area is the gray
        # but it needs to be reachable
        # meaning there needs to be a white spot
        # directly to gray
        # and white spot needs to be wide enough

        goals_to_safe = list(reversed(self.goals))

        current_goal = goals_to_safe[self.current_goal] if len(goals_to_safe) >= self.current_goal +1 else None
        if not current_goal:
            return

        dist_away_from_goal = np.linalg.norm(self.motion.current_pos.list - goals_to_safe[self.current_goal])
        # print("right now:", self.mapper.position)
        # print("go to:", current_goal)
        # print("difference", dist_away_from_goal)
        print("waypoint ", self.current_goal+1)

        if  dist_away_from_goal < ROBOT_SIZE + 0.2:
            self.current_goal += 1

        return self.move_to_force(current_goal)

    # def rotate_around_on_spot(self)
