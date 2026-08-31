from rclpy.node import Node
import os
import json
from collections.abc import Callable


class Phase:
    name: str
    actions: Callable
    start_time: None | float
    end_time: None | float

    def __init__(self, name: str, actions: Callable, once=True):
        self.name = name
        self.actions = actions
        self.start_time = None
        self.end_time = None
        self.once = once # should this run every cycle or just when phase starts?
        self.auto_continue = True

    def run(self):
        self.actions(self)


# TODO: allow there to be a controlling phase, so that different controllers can work in peace
# without the fear that another controller could kick in their phase during theirs

class PhaseManager:
    def __init__(self, node: Node):
        self.node = node

        self.phases:list[Phase] = []
        self.test_done = False
        self.odom_data = []
        self.odom_logs_base_path = f"./odom_logs_real"
        self._current_phase_index = 0

    @property
    def current_phase(self):
        if self._current_phase_index is None or self._current_phase_index >= len(self.phases) or self._current_phase_index < 0:
            return None
    
        return self.phases[self._current_phase_index]
    
    @property
    def now(self):
        return self.node.get_clock().now().nanoseconds / 1e9  # current time in seconds

    def add_phase(self, phase: Phase):
        self.phases.append(phase)
        self.node.logger.info(f"Added Phase {len(self.phases)-1}: {phase.name}")
    
    def add_phases(self, phases: list[Phase]):
        for phase in phases:
            self.add_phase(phase)

    def start_phase(self):
        phase = self.current_phase
        if not phase:
            self.node.logger.info("No phase to start")
            return

        if phase.start_time:
            self.node.logger.info(f"Already started this phase {self._current_phase_index}")
            return

        if self._current_phase_index >= len(self.phases):
            self.node.logger.info("Phase index is at the end!")
            return
        
        self.node.logger.info(f"\n\nPhase {self._current_phase_index}. \"{phase.name}\" started\n")
        self.odom_data = []
        phase.start_time = self.now

        if phase.once: 
            phase.run()

    def skip_to_phase(self, name: str, start=True):
        for index in range(len(self.phases)-1, -1, -1):
            phase = self.phases[index]
            if phase.name == name:
                self.node.logger.info(f'skipping to index {index}' )
                self.skip_to_phase_by_index(index, start)
                return
            
        raise Exception(f"no phase found with name: {name}")
    
    def skip_to_phase_by_index(self, index: int, start=True):
        if self.current_phase and not self.current_phase.end_time:
            self.stop_phase()

        self._current_phase_index = index if index >= 0 else len(self.phases) + index
        if start:
            self.start_phase()

    def start_next_phase(self):
        if self._current_phase_index is None:
            self._current_phase_index = -1
        else:
            self.stop_phase()
    
        self._current_phase_index += 1
        self.start_phase()

    def stop_phase(self):
        phase = self.current_phase

        if phase.start_time is None:
            self.node.logger.warn(f"\nPhase {self._current_phase_index}. \"{phase.name}\" hasn't started yet :(")
            return

        phase.end_time = self.now
        duration = phase.end_time - phase.start_time

        self.node.logger.info(f"\nPhase {self._current_phase_index}. \"{phase.name}\" completed in {duration:.4f}s\n\n")

        log_path = os.path.expanduser(f"{self.odom_logs_base_path}")
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        log_file_name = f"{phase.start_time} - phase {self._current_phase_index}.json"

        with open(
            os.path.join(log_path, log_file_name),
            "w",
        ) as f:
            f.write(json.dumps(self.odom_data))

    def quit_handler(self):
        self.test_done = True


    def control_loop(self):
        if self._current_phase_index is None:
            return

        if self.test_done:
            return

        phase = self.current_phase

        if phase is None:
            return

        if phase.start_time is None:
            self.start_phase()

        now = self.now
        duration = now - phase.start_time
        self.node.logger.info(f"\nPhase {self._current_phase_index}. \"{phase.name}\" running for {duration:.1f}s")
        if phase.end_time:
            left_duration =  now - phase.end_time
            self.node.logger.info(f"Ends in {left_duration:.1f}\n\n")
            if self.now > phase.end_time:
                self.start_next_phase()

        if not phase.once: 
            phase.run()