from typing import Literal

from sensor_msgs.msg import LaserScan
from smart_crazyflie.lib.common import NAMESPACE, FRONT_HEADING, ROBOT_SIZE
import math
import numpy as np
from smart_crazyflie.lib.mapper.display import MapDisplayer
from smart_crazyflie.lib.obstacle_avoider import AVOID_DISTANCE
from smart_crazyflie.lib.motion_controller import MotionController, Position
from rclpy.node import Node
from smart_crazyflie.lib.mapper.cell import Cell, CellState


class MapperAndLocaliser:
    GRID_CELL_SQUARE_SIZE = 0.1  # m
    GRID_SIZE = [10.0, 10.0, 10.0]  # m
    ROBOT_START = Position(GRID_SIZE[0] / 2, GRID_SIZE[1] / 2, GRID_SIZE[2] / 2)

    map_as_matrix: list[list[Cell]]

    def __init__(self, node: Node, motion: MotionController):
        print(f"Mapping \
           { self.GRID_SIZE[0] / self.GRID_CELL_SQUARE_SIZE}x \
            {self.GRID_SIZE[1] / self.GRID_CELL_SQUARE_SIZE}x \
            {self.GRID_SIZE[2] / self.GRID_CELL_SQUARE_SIZE}")

        # mapper depends on....
        self.node = node
        self.motion = motion
        self.scan_sub = self.node.create_subscription(
            LaserScan, f"{NAMESPACE}/scan", self.scan_callback, 10
        )
        self.displayer = MapDisplayer(self.GRID_SIZE, self.GRID_CELL_SQUARE_SIZE)

        # mapper state
        self.robot_radius_cells = self.dist_to_i(ROBOT_SIZE)
        # self.radius_of_close_objects = self.dist_to_i(AVOID_DISTANCE + 0.25)

        self.GRID_SIZE_CELLS = [self.dist_to_i(x) for x in self.GRID_SIZE]

        # TODO: turn into a history mechanism
        # that shows how a certain type of cell is changing over time
        self.travelled_path = []

        self.possible_goals_cells = []
        self.goal_cell = None

        # start mapping...
        self.map_as_matrix = self.initialise_map()
        self.node.create_timer(
            0.1, lambda: self.displayer.draw_grid(self.map_as_matrix)
        )

    @property
    def me_cell(self):
        pos = self.motion.current_pos

        if not pos.is_valid():
            return

        return self.cell_from_pos(pos)

    @property
    def obstacles(self):
        areas = []

        # me_cell = self.me_cell
        # use_small_range = False
        # row_interest = range(max(me_cell[0] - self.radius_of_close_objects, 0), min(me_cell[0] + self.radius_of_close_objects, self.GRID_SIZE_CELLS[0])) if use_small_range else range(0, self.GRID_SIZE_CELLS[0])
        # col_interest = range(max(me_cell[1] - self.radius_of_close_objects, 0), min(me_cell[1] + self.radius_of_close_objects, self.GRID_SIZE_CELLS[1])) if use_small_range else range(0, self.GRID_SIZE_CELLS[1])
        row_interest = range(0, self.GRID_SIZE_CELLS[0])
        col_interest = range(0, self.GRID_SIZE_CELLS[1])

        for row_i in row_interest:
            row = self.map_as_matrix[row_i]
            for col_i in col_interest:
                cell = row[col_i]
                if not cell.me and cell.occupied_status == CellState.OBSTACLE:
                    areas.append([row_i, col_i])

        return areas

    def cell_at(self, cell_i) -> Cell:
        return self.map_as_matrix[cell_i[0]][cell_i[1]]

    def initialise_map(self):
        map = []

        for row, row_location in enumerate(
            np.arange(0, self.GRID_SIZE[0], self.GRID_CELL_SQUARE_SIZE)
        ):
            map.append([])

            for _ in np.arange(0, self.GRID_SIZE[1], self.GRID_CELL_SQUARE_SIZE):
                map[row].append(Cell())

        return map

    def scan_callback(self, msg):
        ranges = msg.ranges
        inc = msg.angle_increment
        for index, range in enumerate(ranges):
            direction = math.degrees(inc * index) + FRONT_HEADING
            self.update_map(range, direction)

        self.update_me()
        self.displayer.draw_grid(self.map_as_matrix)

    def update_me(self):
        me_pos = self.motion.current_pos
        if not me_pos.is_valid():
            return

        me_cell = self.cell_from_pos(me_pos)

        for row_i, row in enumerate(self.map_as_matrix):
            for col_i, cell in enumerate(row):
                cells_away_from_me_cell = math.hypot(
                    row_i - me_cell.x, col_i - me_cell.y
                )
                if [row_i, col_i] == me_cell:
                    cell.me = True
                elif cells_away_from_me_cell < self.robot_radius_cells:
                    cell.override = CellState.ME
                elif cell.me:
                    cell.me = False
                    cell.override = CellState.ME_HISTORY
                    self.travelled_path.append([row_i, col_i])
                elif cell.override == CellState.ME:
                    cell.override = None

        direction_pointer = self.cells_hit_by_range_beam(me_pos.list, 0, 0.4)
        for cell in direction_pointer:
            self.map_as_matrix[cell[0]][cell[1]].override = CellState.ME

    def cell_from_pos(self, pos: Position):
        map_grid_pos = pos.list - self.ROBOT_START.list
        cell = Position(*[self.dist_to_i(x) for x in map_grid_pos])
        return cell

    def dist_to_i(self, distance):
        return math.floor(distance / self.GRID_CELL_SQUARE_SIZE)

    def i_to_dist(self, i):
        # To the centre of the grid cell
        return (i + 0.5) * self.GRID_CELL_SQUARE_SIZE

    def cell_to_pos(self, cell):
        return [self.i_to_dist(cell[0]), self.i_to_dist(cell[1])]

    def update(
        self,
        cell_state: CellState,
        new_cells: list[Cell],
        update_type: Literal["add", "replace"] = "add",
        previous_cells: list[Cell] | None = None,
    ):
        if update_type == "replace":
            if previous_cells:
                # just replace these cells
                pass
            else:
                for row_i, row in enumerate(self.map_as_matrix):
                    for col_i, cell in enumerate(row):
                        if cell_state in cell.states:
                            cell.states.remove(cell_state)

        for new_cell in new_cells:
            new_cell.states.add(cell_state)

    def update_map(self, lidar_range, in_direction):
        # get cells in range in direction
        if lidar_range == float("inf"):
            return

        me_pos = self.motion.current_pos
        if not me_pos:
            return

        cells = self.cells_hit_by_range_beam(
            me_pos, in_direction + self.motion.current_rot.yaw, lidar_range
        )
        if len(cells) < 2:
            return

        try:
            for index, cell_pos in enumerate(cells):
                cell: Cell = self.map_as_matrix[cell_pos[0]][cell_pos[1]]
                if index == len(cells) - 1:
                    cell.update_probability(obstacle=True)
                else:
                    cell.update_probability(obstacle=False)

        except Exception as e:
            # print(e)
            print("no real index", cell_pos, lidar_range)
            raise Exception(e)

        # unknown_cells = self.cells_hit_by_range_beam(
        #     self.cell_to_pos(cells[-1]) + [self.position[-1]],
        #     in_direction,
        #     max(self.GRID_SIZE) ** 2,
        # )
        # if len(unknown_cells) < 2:
        #     return

        # for index, cell_pos in enumerate(unknown_cells[1:]):
        #     try:
        #         cell: Cell = self.map_as_grid[cell_pos[0]][cell_pos[1]]
        #         if cell.occupied_status == CellState.FREE:
        #             cell.reset()

        #     except Exception as e:
        #         # print(e)
        #         print("no real index", cell_pos, lidar_range)
        #         # raise Exception(e)

    def cells_hit_by_range_beam(
        self,
        beam_start_location: Position,
        beam_direction_degrees: float,
        beam_length: float,
    ) -> list[tuple[int, int]]:
        x0, y0, z0 = beam_start_location.list
        cell_size = self.GRID_CELL_SQUARE_SIZE

        # Normalize direction
        angle_rad = math.radians(beam_direction_degrees)

        dx = math.cos(angle_rad)
        dy = math.sin(angle_rad)

        mag = math.hypot(dx, dy)
        if mag == 0:
            raise ValueError("Direction vector cannot be zero.")

        dx /= mag
        dy /= mag

        # Beam end point
        x1 = x0 + dx * beam_length
        y1 = y0 + dy * beam_length

        # Current cell
        ix = int(math.floor(x0 / cell_size))
        iy = int(math.floor(y0 / cell_size))
        # print("start cell", ix, iy)

        # End cell
        end_ix = int(math.floor(x1 / cell_size))
        end_iy = int(math.floor(y1 / cell_size))
        # print("end cell", end_ix, end_iy)

        cells = [(ix, iy)]

        # Step direction
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1

        # Distance to first vertical boundary
        if dx != 0:
            next_vert = (ix + (dx > 0)) * cell_size
            t_max_x = (next_vert - x0) / dx
            t_delta_x = cell_size / abs(dx)
        else:
            t_max_x = float("inf")
            t_delta_x = float("inf")

        # Distance to first horizontal boundary
        if dy != 0:
            next_horiz = (iy + (dy > 0)) * cell_size
            t_max_y = (next_horiz - y0) / dy
            t_delta_y = cell_size / abs(dy)
        else:
            t_max_y = float("inf")
            t_delta_y = float("inf")

        max_t = beam_length

        while (ix, iy) != (end_ix, end_iy):

            if t_max_x < t_max_y:
                ix += step_x
                t = t_max_x
                t_max_x += t_delta_x
            else:
                iy += step_y
                t = t_max_y
                t_max_y += t_delta_y

            if t > max_t:
                break

            if (
                ix < 0
                or ix >= self.GRID_SIZE_CELLS[0]
                or iy < 0
                or iy >= self.GRID_SIZE_CELLS[1]
            ):
                break

            cells.append((ix, iy))

        return cells

    def save_map(self):
        self.displayer.export_image(
            self.map_as_matrix, self.node.get_clock().now().nanoseconds / 1e9
        )

    def is_reachable(self, cell_i):
        # reachable  = free cell
        # surrounded by at least one free
        # not by surrounded any occupied cells

        surrounding = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        has_free = False

        for cell_shift in surrounding:
            try:
                cell = self.map_as_matrix[cell_i[0] + cell_shift[0]][
                    cell_i[1] + cell_shift[1]
                ]
                if cell.occupied_status == CellState.FREE:
                    has_free = True

                if cell.occupied_status == CellState.OBSTACLE:
                    return False
            except IndexError as e:
                return False

        return has_free

    def reachable_unknown_areas(self) -> list[tuple[int, int]]:
        # where white touches gray
        areas = []

        for row_i, row in enumerate(self.map_as_matrix):
            for col_i, cell in enumerate(row):
                if (
                    self.is_reachable([row_i, col_i])
                    and cell.occupied_status == CellState.UNKNOWN
                ):
                    areas.append([row_i, col_i])
                    cell.override = CellState.ROAM_DEST
                elif cell.override == CellState.ROAM_DEST:
                    cell.override = None

        return areas
