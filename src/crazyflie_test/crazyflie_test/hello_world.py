"""Takeoff-hover-land for one CF. Useful to validate hardware config."""

from crazyflie_py import Crazyswarm


TAKEOFF_DURATION = 5.0
HOVER_DURATION = 5.0


def main():
    try:
        swarm = Crazyswarm()
        timeHelper = swarm.timeHelper
        cf = swarm.allcfs.crazyflies[0]
        cf.takeoff(targetHeight=0.6, duration=TAKEOFF_DURATION)
        timeHelper.sleep(2*TAKEOFF_DURATION)

    except KeyboardInterrupt:
        swarm.allcfs.emergency()


if __name__ == '__main__':
    main()