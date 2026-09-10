# Kinematics

Kinematics extends [assemblies](assemble.html): generalized coordinates, such as a hinge angle or actuator travel, determine part placement. Ordinary ZenCad operations build the geometry; kinematic joints control where it is placed.

## Two units per joint

A kinematic component consists of two units in relative motion:

- The joint object itself inherits `kinematic_unit` and serves as the input unit. Its `location` places the joint relative to its parent.
- `joint.output` is the output unit, parented to the input. Its placement relative to the input is determined by the joint coordinates.

```text
parent
└── joint                 input: joint mounting
    └── joint.output      output: rotation or translation
        └── payload       part or subsequent joint
```

`joint.add(shape)` attaches geometry to the input, such as an actuator housing. `joint.output.add(shape)` attaches it to the moving output. `joint.link(child)` also attaches to the **output**, whereas ordinary `unit.link(child)` attaches directly to that unit.

Use `parent=joint.output` in a child's constructor to make it follow the output. `parent=joint` attaches it to the input instead.

## Rotary and linear joints

Import these classes from `zencad.assemble`:

| Joint | Coordinate | Output motion |
| --- | --- | --- |
| `rotator(axis=...)` | `set_coord(angle)`, radians | Rotation about a local input axis |
| `actuator(axis=...)` | `set_coord(distance)`, model length units | Translation along a local input axis |

The axis is normalized. `mul` scales the coordinate: the physical angle or displacement is `coord * mul`. `location` places the input; `set_coord()` changes the output relative to it. Single-coordinate joints return `1` from `dim()` and also accept `set_coords([value])`.

A rotating arm:

```python
from zencad import *
from zencad.assemble import unit, rotator

base = unit()
joint = rotator(axis=(0, 0, 1), parent=base)
joint.add(cylinder(3, 2, center=True))
joint.output.add(box(20, 2, 2).back(1).down(1))
tip = unit(parent=joint.output, location=translate(20, 0, 0))

base.location_update(deep=True, view=False)
joint.set_coord(deg(90), view=False)
position = tip.global_location.translation()
assert abs(position.x) < 1e-7
assert abs(position.y - 20) < 1e-7

display(base)
show()
```

The arm geometry stays unchanged; its placement changes. `global_location` includes all ancestors. After manually changing the hierarchy or local placements, call `base.location_update(deep=True)`. `view=False` is useful for calculations without presentation updates; use normal updates for displayed models.

For animation, construct the assembly before `show()` and change joint coordinates in the callback. Examples live in `zencad/examples/4.Assemble`; see [Animation](animate.html) for input handling.

## Kinematic chains and trees

ZenCad itself contains `kinematic_chain` in `zencad.libs.kinematic`. It is an algorithmic view of **one path** through the assembly tree, not another container for the parts.

`kinematic_chain(distant, proxymal=None)` follows `parent` links from the terminal unit `distant` to the initial unit `proxymal`, including it. With no initial unit, it walks to the root. `proxymal` is the actual API spelling; this unit must be an ancestor of the terminal unit.

- `getchain()` returns every unit on the path, including fixed intermediate units.
- `kinematic_pairs` contains only kinematic joints; `chain[i]` indexes this list.
- Ordering runs **from the tip towards the base**. Increments and matrix columns follow this order for single-coordinate joints.

There is no separate `kinematic_tree` class. Ordinary `unit` links form the tree: an input or output can have multiple children. Construct a chain to a shared base for each end effector of interest. Changing a coordinate shared by several branches changes all dependent descendant placements.

## Sensitivities and Jacobians

A chain computes the local dependence of end-effector motion on joint coordinates:

| Method | Result |
| --- | --- |
| `sensivity(basis=None)` | A list of `screw` objects with angular `.ang` and linear `.lin` components |
| `sensivity_jacobian(basis=None)` | A `6 × N` NumPy matrix: angular components in the first three rows, linear components in the last three |
| `translation_sensivity_jacobian(basis=None)` | A `3 × N` NumPy matrix of linear components |
| `apply_step(increments)` | Adds coordinate increments in Jacobian-column order |
| `apply(speeds, delta)` | Adds `speed * delta` to each coordinate |

`sensivity` is the actual API spelling. Without `basis`, sensitivities are expressed in the terminal unit's frame; `basis=base` expresses them in that unit's frame. Update tree placements before calculating. Supply one increment or speed per Jacobian column: joints follow `kinematic_pairs` order, and coordinates within each joint are reversed relative to `set_coords()`.

```python
from zencad import *
from zencad.assemble import unit, rotator, actuator
from zencad.libs.kinematic import kinematic_chain

base = unit()
hinge = rotator(axis=(0, 0, 1), parent=base)
slide = actuator(
    axis=(1, 0, 0), parent=hinge.output, location=translate(10, 0, 0)
)
tip = unit(parent=slide.output)
base.location_update(deep=True, view=False)
slide.set_coord(2, view=False)

chain = kinematic_chain(tip, proxymal=base)
assert chain.kinematic_pairs == [slide, hinge]
jacobian = chain.translation_sensivity_jacobian(basis=base)
assert jacobian.shape == (3, 2)
assert abs(jacobian[0, 0] - 1) < 1e-7
assert abs(jacobian[1, 1] - 12) < 1e-7

chain.apply_step([1, 0])
assert abs(tip.global_location.translation().x - 13) < 1e-7
```

The first column describes the linear actuator; the second describes the hinge. At the initial reach of `12`, a small hinge rotation produces Y velocity with a coefficient of `12`.

To track a local frame inside an intermediate unit, use `sensivity2(body, local, basis=None)`, `sensitivity_jacobian2(...)` or `translation_sensitivity_jacobian2(...)`. These methods can analyze a frame other than the chain's terminal frame, including a joint input or a unit on a sibling branch. Coordinates that do not affect the selected unit produce zero columns. `basis` changes the frame in which absolute velocity is expressed; its own motion is not subtracted.

In `zencad/examples/4.Assemble/robot-arm.py`, a chain of rotary joints automatically follows a red ball along a closed spatial curve. The position Jacobian and damped least squares determine joint velocities; `chain.apply()` applies them in matrix-column order. The example controls the tip position, not its orientation.


## Support boundaries

`spherical_rotator` has two coordinates: `set_coords([yaw, pitch])` sets `rotateZ(yaw) * rotateY(pitch)`. Angles are in radians; separate `set_yaw()` and `set_pitch()` methods are available. `dim()` returns `2`, and `get_coords()` returns `(yaw, pitch)`. `senses()` returns yaw and pitch angular sensitivities in the joint output frame, accounting for the current angles. This is a two-axis rotation, not a three-coordinate parameterization of arbitrary orientation.

`planemover.set_coords([x, y])` sets an XY translation; `get_coords()` returns `(x, y)`, and `senses()` returns linear sensitivities along X and Y.

The chain preserves reversed sensitivity order within each pair: pitch then yaw for `spherical_rotator`, Y then X for `planemover`. `apply_step()` and `apply()` support mixed chains containing these joints, `rotator`, and `actuator`. The input vector length equals the sum of joint `dim()` values. Length and finite values are validated before changing coordinates.
