#!/usr/bin/env python3
"""A robot arm follows a moving ball using the position Jacobian.

The target runs on a closed spatial curve; only the end position is controlled, not orientation.
"""

from zencad import *
from zencad.assemble import unit, rotator
from zencad.libs.kinematic import kinematic_chain
import math
import numpy as np


base = unit(parts=[cylinder(18, 6)], name="base")
yaw = rotator(axis=(0, 0, 1), parent=base, location=up(6), name="yaw")
parent = yaw.output
joints = [yaw]

for index, axis in enumerate(((0, 1, 0), (1, 0, 0), (0, 1, 0), (1, 0, 0))):
    joint = rotator(axis=axis, parent=parent, name=f"joint-{index + 1}")
    joint.add(cylinder(7, 16, center=True).transform(short_rotate((0, 0, 1), axis)),
              color=(0.25, 0.3, 0.35))
    joint.output.add(cylinder(4, 40), color=(0.85, 0.65, 0.2))
    parent = unit(parent=joint.output, location=up(40))
    joints.append(joint)

tip = parent
tip.add(sphere(5), color=(0.2, 0.8, 0.3))
# Start bent so the arm can move towards the target along all three axes.
for joint, coordinate in zip(joints, (0.2, 0.6, -0.5, 0.7, 0.4)):
    joint.set_coord(coordinate)
base.location_update(deep=True)
chain = kinematic_chain(tip, base)


def target_position(t):
    return np.array([60 + 20 * math.cos(t),
                     30 * math.sin(t),
                     85 + 15 * math.sin(2 * t)])


disp(base)
target_controller = disp(sphere(6), color.red)
target_controller.relocate(translate(*target_position(0)))
elapsed = 0.0


def animate(state):
    global elapsed
    delta = min(max(state.delta, 0.0), 0.05)
    elapsed += delta
    target = target_position(elapsed * 0.4)
    current = np.array(tip.global_location.translation().to_array())
    error = target - current
    jacobian = chain.translation_sensivity_jacobian(basis=base)

    # Damped least squares stays bounded near straight/singular poses.
    damping = 2.0
    speeds = jacobian.T @ np.linalg.solve(
        jacobian @ jacobian.T + damping**2 * np.eye(3), 6.0 * error
    )
    speeds *= min(1.0, 2.0 / max(float(np.max(np.abs(speeds))), 1e-12))
    # Column order is distal-to-base; apply() uses that same order.
    chain.apply(speeds, delta)
    target_controller.relocate(translate(*target))


show(animate=animate)
