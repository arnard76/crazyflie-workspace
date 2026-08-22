"""Takeoff-hover-land for one CF. Useful to validate hardware config."""

# import math

from crazyflie_py import Crazyswarm
from crazyflie_py.crazyflie import Crazyflie


def main():
    swarm = Crazyswarm()
    try:
        while True:
            timeHelper = swarm.timeHelper
            # cf:Crazyflie = swarm.allcfs.crazyflies[0]
            timeHelper.sleep(3)
    except Exception as e:
        print(e)
        print("Call Emergency")
        swarm.allcfs.emergency()
    except KeyboardInterrupt:
        print("Call Emergency")
        swarm.allcfs.emergency()


if __name__ == '__main__':
    main()