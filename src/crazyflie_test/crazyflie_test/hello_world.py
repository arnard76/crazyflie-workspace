"""Takeoff-hover-land for one CF. Useful to validate hardware config."""

# import math

from crazyflie_py import Crazyswarm
from crazyflie_py.crazyflie import Crazyflie


TAKEOFF_DURATION = 3.0
HOVER_DURATION = 1.0


def main():
    swarm = Crazyswarm()
    try:
        timeHelper = swarm.timeHelper
        cf:Crazyflie = swarm.allcfs.crazyflies[0]
        cf.takeoff(targetHeight=0.45, duration=TAKEOFF_DURATION)
        timeHelper.sleep(3*TAKEOFF_DURATION)
        print("completed takeoff")
        # cf.cmdPosition((1.0, 1.0, 1.0), yaw=math.pi/2)
        cf.notifySetpointsStop()
        cf.land(0.04, TAKEOFF_DURATION)
        timeHelper.sleep(3*TAKEOFF_DURATION)
        print("completed land")
    except Exception as e:
        print(e)
        print("Call Emergency")
        swarm.allcfs.emergency()
    except KeyboardInterrupt:
        print("Call Emergency")
        swarm.allcfs.emergency()


if __name__ == '__main__':
    main()