#!/usr/bin/env python

from pathlib import Path

from crazyflie_py import Crazyswarm
from crazyflie_py.crazyflie import Crazyflie
from crazyflie_py.uav_trajectory import Trajectory
import numpy as np


def main():
    swarm = Crazyswarm()
    timeHelper = swarm.timeHelper
    # allcfs = swarm.allcfs

    traj1 = Trajectory()
    traj1.loadcsv(Path(__file__).parent / 'data/figure8.csv')

    # enable logging

    TRIALS = 1
    TIMESCALE = 1.0

    try:
        cf:Crazyflie = swarm.allcfs.crazyflies[0]
        cf.setParam('usd.logging', 1)

        for i in range(TRIALS):
            cf.uploadTrajectory(0, 0, traj1)

            cf.takeoff(targetHeight=1.0, duration=2.0)
            timeHelper.sleep(2.5)
            pos = np.array(cf.initialPosition) + np.array([0, 0, 1.0])
            cf.goTo(pos, 0, 2.0)
            timeHelper.sleep(2.5)

            cf.startTrajectory(0, timescale=TIMESCALE)
            timeHelper.sleep(traj1.duration * TIMESCALE + 2.0)
            # allcfs.startTrajectory(0, timescale=TIMESCALE, reverse=True)
            # timeHelper.sleep(traj1.duration * TIMESCALE + 2.0)

            cf.land(targetHeight=0.06, duration=2.0)
            timeHelper.sleep(3.0)

        # disable logging
        cf.setParam('usd.logging', 0)
    except Exception as e:
        print(e)
        print("Call Emergency")
        swarm.allcfs.emergency()
    except KeyboardInterrupt:
        print("Call Emergency")
        swarm.allcfs.emergency()


if __name__ == '__main__':
    main()