## Setup

Mostly just follow Crazyswarm2 tutorial: https://imrclab.github.io/crazyswarm2/installation.html

Notes:

* Choose Ubuntu-24.04 with Jazzy
* Installed via WSL on Windows Device
* Install pip3 via sudo apt install python3-pip
* usbipd-win is needed to forward USB devices connected to windows machine to WSL/linux: https://github.com/dorssel/usbipd-win/wiki/WSL-support/ 
* Install Cython
* Intellisense in VS Code: https://share.google/aimode/F97tgVNr9qz0fYPDh 

Crazyradio 2.0 tutorial: https://www.bitcraze.io/documentation/tutorials/getting-started-with-crazyradio-2-0/ 

Introduction tutorials: https://imrclab.github.io/crazyswarm2/tutorials.html# 
* Includes teleoperation
* Visualisation with rviz
* Simple Mapping with SLAM toolbox


## Development Commands

Setup workspace:

```bash
source /opt/ros/jazzy/setup.bash
# after build, do: source ./install/setup.bash
export PYTHONPATH=~/crazyflie-firmware/build:$PYTHONPATH
# python3 -m venv venv # if you haven't before
source venv/bin/activate
```

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

## Research

Related Research Documentation: https://docs.google.com/document/d/1LjIgr2-3v0vMCZJ1xNWqVj5WK5T3llzlzFar9guhgWY/edit?tab=t.pxht6snb1054 


