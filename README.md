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
* PS3 for manual controller: https://share.google/aimode/67dpqKSP3JquDCim7

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

# install rosbridge: https://wiki.ros.org/rosbridge_suite
# learn ros2 bridge: https://foxglove.dev/blog/using-rosbridge-with-ros2
sudo apt-get install ros-jazzy-rosbridge-server
```

Create and activate a virtual environment for workspace python code:

```bash
# one-time - if you haven't before,
# ROS2 packages are installed globally hence arg
python3 -m venv venv --system-site-packages 
source venv/bin/activate # for every terminal session
```

## General ROS2 Commands

Build ROS2 packages with intellisense & references

```bash
colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release
```

Run ROS2 package
```bash
ros2 run <packagename> <scriptname>
ros2 run tf2_ros static_transform_publisher --x 1.0 --y 2.0 --z 0.0 --roll 0.0 --pitch 0.0 --yaw 0.0 --frame-id base_link --child-frame-id my_new_frame
```

OR without rebuild, try:
```bash
python src/<packagename>/<packagename>/<scriptname>.py
```

Launch multiple nodes together:
```bash
ros2 launch <packagename> <launchfilename>
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
ros2 launch foxglove_bridge foxglove_bridge_launch.xml

# Crazyswarm args
ros2 launch <package_name> launch.py script:=<script_name> backend:=sim 
```

## Debugging & Analysis

rqt - GUI for inspecting and managing ros2

rosbag 2

[foxglove](https://foxglove.dev/home)
    * ```ros2 launch foxglove_bridge foxglove_bridge_launch.xml```

## Run Smart Crazyflie App

```bash
ros2 launch smart_crazyflie launch.py backend:=sim script:=main
ros2 launch smart_crazyflie launch.py script:=main
```

It includes: Crazyflie Launch, Crazyswarm2 App, ROSbridge, Foxglove, Static & Moving Frames 


## Research

Related Research Documentation: https://docs.google.com/document/d/1LjIgr2-3v0vMCZJ1xNWqVj5WK5T3llzlzFar9guhgWY/edit?tab=t.pxht6snb1054 


