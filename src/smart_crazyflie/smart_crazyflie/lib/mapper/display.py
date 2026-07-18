import os
import random
import time
from smart_crazyflie.lib.mapper.cell import CellState, Cell
import cv2
import numpy as np

# ANSI background colors
COLORS = {
    CellState.OBSTACLE: [0, 0, 0],  # black
    CellState.UNKNOWN: [100, 100, 100],  # gray
    CellState.FREE: [255, 255, 255],  # white

    CellState.ME: [128, 0, 128],
    CellState.ME_HISTORY: [100, 25, 100],

    CellState.ROAM_DEST: [51, 112, 6],
    CellState.POSSIBLE_MISSION_OBJECTIVE: [104, 43, 159],
    CellState.MISSION_OBJECTIVE: [255, 0, 255],
    CellState.MOTION_FORCE: [252, 57, 3],
    
    CellState.CLOSE_OBSTACLE: [20, 0, 150]
}


class MapDisplayer:
    def __init__(self, grid_size: list[float], cell_size: float):
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.window = "Robot Map"

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")

    def format_raw_grid_image(self, grid_image):
        scale_width = 500
        scale_height = 500
        large_image = cv2.resize(
            grid_image, (scale_width, scale_height), interpolation=cv2.INTER_NEAREST
        )
        return large_image

    def draw_grid(self, grid: list[list[Cell]]):
        grid_matrix_image = np.asarray(
            [[COLORS[c.status] for c in row] for row in grid]
        ).astype(np.uint8)

        cv2.imshow(self.window, self.format_raw_grid_image(grid_matrix_image))
        cv2.waitKey(1)

    def export_image(self, grid, timestamp=None):
        grid_matrix_image = np.asarray(
            [[COLORS[c.status] for c in row] for row in grid]
        ).astype(np.uint8)
        image = self.format_raw_grid_image(grid_matrix_image)
        snap_path = os.path.join("map", f'map-{timestamp or ""}.png')
        cv2.imwrite(snap_path, image)

