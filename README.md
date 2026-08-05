## Setup

### Setup Crazyswarm2
Mostly just follow Crazyswarm2 tutorial: https://imrclab.github.io/crazyswarm2/installation.html

Notes:

* Choose Ubuntu-24.04 with Jazzy
* Installed via WSL on Windows Device
* Install pip3 via sudo apt install python3-pip
* usbipd-win is needed to forward USB devices connected to windows machine to WSL/linux: https://github.com/dorssel/usbipd-win/wiki/WSL-support/ 
* Install Cython
* Intellisense in VS Code: https://share.google/aimode/F97tgVNr9qz0fYPDh 

### Setup Crazyradio 2.0
follow the tutorial: https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyradio-2-0/ 


### Learn Crazyswarm2
Introduction tutorials: https://imrclab.github.io/crazyswarm2/tutorials.html# 
* Includes teleoperation
* Visualisation with rviz
* Simple Mapping with SLAM toolbox

### Setup development workspace
Automatically setup new terminal windows by adding these two lines at the end of `~/.bashrc` file. These commands make ros2 and the firmware package available.

```bash
source /opt/ros/jazzy/setup.bash
# place the crazyflie-firmware repository in user root folder ~/
export PYTHONPATH=~/crazyflie-firmware/build:$PYTHONPATH
```

Create and activate a virtual environment for workspace python code:

```bash
python3 -m venv venv # one-time - if you haven't before
source venv/bin/activate # for every terminal session
```

## Development Commands

Build ROS2 packages with intellisense & references

```bash
colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release
```

Run ROS2 package
```bash
ros2 run <packagename> <scriptname>
```
OR without rebuild, try:
```bash
python src/<packagename>/<packagename>/<scriptname>.py
```

Run Crazyswarm2 app
```bash
ros2 launch <package_name> launch.py script:=<script_name> backend:=sim
```

## Debugging & Analysis Tools

rqt - GUI for inspecting and managing ros2

## Research

Related Research Documentation: https://docs.google.com/document/d/1LjIgr2-3v0vMCZJ1xNWqVj5WK5T3llzlzFar9guhgWY/edit?tab=t.pxht6snb1054 


