from enum import Enum


class CellState(Enum):
    OBSTACLE = 0
    UNKNOWN = 1
    FREE = 2
    ME = 3
    ME_HISTORY = 4
    CLOSE_OBSTACLE = 5
    ROAM_DEST = 8
    POSSIBLE_MISSION_OBJECTIVE = 10
    MISSION_OBJECTIVE = 11
    MOTION_FORCE = 12


class Cell:
    PROBABILITY_THRESHOLD_ASSUME_OCCUPIED = 0.7
    PROBABILITY_THRESHOLD_ASSUME_MISSION = 0.8

    probability_occupied = 0.5
    mission_objective_likeliness_score = 0.0
    seen = False
    override: CellState | None = None
    me = False

    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)

    def reset(self):
        self.probability_occupied = 0.5
        self.seen = False
        self.me = False

    def update_probability(self, obstacle: bool):
        self.seen = True
        
        if obstacle:
            self.probability_occupied += 0.3
        elif self.probability_occupied < 0.9:
            self.probability_occupied -= 0.1
        else:
            self.probability_occupied -= 0.001

        self.probability_occupied = self.clamp(self.probability_occupied, 0, 1)

    def update_probability_mission_objective(self, in_red_line: bool):
        if in_red_line and self.occupied_status==CellState.OBSTACLE:
            self.mission_objective_likeliness_score += 0.3
        else:
            self.mission_objective_likeliness_score -= 0.2
        
    @property
    def occupied_status(self):
        if not self.seen:
            return CellState.UNKNOWN

        if self.probability_occupied > self.PROBABILITY_THRESHOLD_ASSUME_OCCUPIED:
            return CellState.OBSTACLE

        return CellState.FREE
    
    @property
    def status(self):
        if self.override:
            return self.override
        
        if self.me:
            return CellState.ME
        
        if self.mission_objective_likeliness_score > self.PROBABILITY_THRESHOLD_ASSUME_MISSION:
            return CellState.POSSIBLE_MISSION_OBJECTIVE
        
        return self.occupied_status
