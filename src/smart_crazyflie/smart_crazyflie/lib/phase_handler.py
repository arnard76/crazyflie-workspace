from rclpy.node import Node
import os
import json

# TODO: create a Phase class, instead of using unstructured dictionaries everywhere
# TODO: allow there to be a controlling phase, so that different controllers can work in peace
# without the fear that another controller could kick in their phase during theirs

class PhaseManager:
    def __init__(self, node: Node):
        self.node = node
        self.current_phase_index = None

        self.phases = []
        self.test_done = False
        self.odom_data = []
        self.odom_logs_base_path = f"./odom_logs_real"

    @property
    def current_phase(self):
        if self.current_phase_index is None or self.current_phase_index >= len(self.phases) or self.current_phase_index < 0:
            return None
    
        return self.phases[self.current_phase_index]
    
    @property
    def now(self):
        return self.node.get_clock().now().nanoseconds / 1e9  # current time in seconds

    def add_phase(self, phase: dict):
        self.phases.append(phase | {"start_time": None, "end_time": None})
        print(f"Added Phase {len(self.phases)-1}: {phase['name']}")
    
    def add_phases(self, phases: list[dict]):
        for phase in phases:
            self.add_phase(phase)

    def start_phase(self):
        if not self.current_phase:
            print("No phase to start")
            return

        if self.current_phase["start_time"]:
            print(f"Already started this phase {self.current_phase_index}")
            return

        if self.current_phase_index >= len(self.phases):
            print("Phase index is at the end!")
            return
        
        print(f"\n\nPhase {self.current_phase_index}. \"{self.current_phase['name']}\" started\n")
        self.odom_data = []
        self.phases[self.current_phase_index]["start_time"] = self.now

    def skip_to_phase(self, name: str, start=True):
        for index in range(len(self.phases)-1, -1, -1):
            phase = self.phases[index]
            if phase["name"] == name:
                print(f'skipping to index {index}' )
                self.skip_to_phase_by_index(index, start)
                return
            
        raise Exception(f"no phase found with name: {name}")
    
    def skip_to_phase_by_index(self, index: int, start=True):
        if self.current_phase and not self.current_phase["end_time"]:
            self.stop_phase()

        self.current_phase_index = index
        if start:
            self.start_phase()

    def start_next_phase(self):
        if self.current_phase_index is None:
            self.current_phase_index = -1
        else:
            self.stop_phase()
    
        self.current_phase_index += 1
        if self.current_phase_index >= len(self.phases):
            self.test_done = True

        self.start_phase()

    def stop_phase(self):
        print(f"\nPhase {self.current_phase_index}. \"{self.current_phase['name']}\"")
        self.phases[self.current_phase_index]["end_time"] = self.now
        duration = self.current_phase["end_time"] - self.current_phase["start_time"]

        print(f"\nPhase {self.current_phase_index}. \"{self.current_phase['name']}\" completed in {duration:.4f}s\n\n")

        log_path = os.path.expanduser(f"{self.odom_logs_base_path}")
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        log_file_name = f"{self.current_phase['start_time']} - phase {self.current_phase_index}.json"

        with open(
            os.path.join(log_path, log_file_name),
            "w",
        ) as f:
            f.write(json.dumps(self.odom_data))

    def control_loop(self):
        if self.current_phase_index is None:
            return

        if self.current_phase_index >= len(self.phases):
            self.test_done = True

        if self.test_done:
            return
        
        if not self.current_phase["start_time"]:
            self.start_phase()

        if self.current_phase["end_time"]:
            return

        self.current_phase["actions"]()