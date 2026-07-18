import heapq
import numpy as np
import matplotlib.pyplot as plt
from smart_crazyflie.lib.mapper.cell import Cell, CellState


class AStarPlanner:
    def __init__(self, occupancy_map):
        """
        occupancy_map:
            0 = free
            1 = obstacle
        """
        self.map = occupancy_map
        self.rows = len(occupancy_map)
        self.cols = len(occupancy_map[0])

        # 8-connected grid movement
        self.moves = [
            (-1, 0, 1.0),   # up
            (1, 0, 1.0),    # down
            (0, -1, 1.0),   # left
            (0, 1, 1.0),    # right
            # (-1, -1, 1.414),
            # (-1, 1, 1.414),
            # (1, -1, 1.414),
            # (1, 1, 1.414),
        ]

    def heuristic(self, a, b):
        """Euclidean distance heuristic"""
        return np.hypot(b[0] - a[0], b[1] - a[1])

    def in_bounds(self, node):
        r, c = node
        return 0 <= r < self.rows and 0 <= c < self.cols

    def is_free(self, node):
        r, c = node
        cell:Cell = self.map[r][c]
        return cell.occupied_status == CellState.FREE


    def neighbors(self, node):
        result = []

        for dr, dc, cost in self.moves:
            nr = node[0] + dr
            nc = node[1] + dc
            neighbor = (nr, nc)

            if self.in_bounds(neighbor) and self.is_free(neighbor):
                result.append((neighbor, cost))

        return result

    def reconstruct_path(self, came_from, current):
        path = [current]

        while current in came_from:
            current = came_from[current]
            path.append(current)

        path.reverse()
        return path

    def plan(self, start, goal):
        """
        start, goal: (row, col)
        """

        start = (start[0], start[1])
        goal = tuple(goal)

        open_set = []
        heapq.heappush(open_set, (0, start))

        came_from = {}

        g_cost = {start: 0}
        f_cost = {start: self.heuristic(start, goal)}

        visited = set()

        while open_set:
            _, current = heapq.heappop(open_set)
            print("current ", current)
            print("goal ", goal)
            if current == goal:
                return self.reconstruct_path(came_from, current)

            visited.add(current)

            for neighbor, move_cost in self.neighbors(current):

                tentative_g = g_cost[current] + move_cost

                if neighbor in visited and tentative_g >= g_cost.get(neighbor, np.inf):
                    continue

                if tentative_g < g_cost.get(neighbor, np.inf):

                    came_from[neighbor] = current
                    g_cost[neighbor] = tentative_g
                    f_cost[neighbor] = tentative_g + self.heuristic(neighbor, goal)

                    heapq.heappush(open_set, (f_cost[neighbor], neighbor))

        return None


def visualize(map_data, path, start, goal):
    display = np.copy(map_data)

    plt.figure(figsize=(8, 8))
    plt.imshow(display, cmap='gray_r')

    if path:
        path = np.array(path)
        plt.plot(path[:, 1], path[:, 0], 'b-', linewidth=2, label='Path')

    plt.plot(start[1], start[0], 'go', markersize=10, label='Start')
    plt.plot(goal[1], goal[0], 'ro', markersize=10, label='Goal')

    plt.legend()
    plt.title("A* Path Planning")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":

    # Create occupancy map
    grid = np.zeros((50, 50), dtype=int)

    # Add obstacles
    grid[10:40, 25] = 1
    grid[25, 10:35] = 1

    # Gap in obstacle
    grid[30:35, 25] = 0

    start = (5, 5)
    goal = (45, 45)

    planner = AStarPlanner(grid)

    path = planner.plan(start, goal)

    if path:
        print(f"Path found with {len(path)} points")
    else:
        print("No path found")

    visualize(grid, path, start, goal)