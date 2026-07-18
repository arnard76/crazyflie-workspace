import os
NAMESPACE = "T" + os.environ.get("ROS_DOMAIN_ID") if os.environ.get("ROS_DOMAIN_ID") else ""

### ROBOT PARAMETERS ###
ROBOT_MASS = 0.029 # kg
ROBOT_DIMENSIONS = [0.092, 0.092, 0.029]  # m
ROBOT_SIZE = ROBOT_DIMENSIONS[0]  # m
FRONT_HEADING = 0  # degrees