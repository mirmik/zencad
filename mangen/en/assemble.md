# Hierarchical assemblies

Displaying a complex or animated scene often involves many related interactive objects moving relative to one another according to particular rules.

ZenCad provides the `zencad.assemble` library and its main tool, `zencad.assemble.unit`, to make this easier.

------------------------------------------------------------
## Assembly unit (zencad.assemble.unit)
An assembly unit has its own local coordinate system, relative to which its interactive objects and child units are placed. Units can form a tree, with each unit positioned relative to its parent (`unit.parent`). A unit without a parent is positioned relative to the global coordinate system.

A unit holds two transforms: `location` and `global_location`.

- `location` sets placement relative to the parent. It can be changed directly or with `relocate`.
- `global_location` is the placement in global coordinates, used for display. It is derived from the tree of `unit.location` values and can be updated with `location_update`, `relocate` and other operations.

------------------
## Adding an object
Creates an interactive object from the geometric object _obj_ and attaches it to the unit.

If an interactive object is passed, the unit takes control of its placement.

Signature:
```python
u.add(obj, color=None)
```

Example:
```
m = box(10)
i = box(10).right(20)
u.add(m)
u.add(i)
``` 

--------------------------------
## Adding a child unit
Makes _u_ the parent of _child_. The placement of objects in _child_ and its descendants will then take _u_'s placement into account.

Signature:
```python
u.link(child)
```

Example:
```python
from zencad.assemble import unit

u = unit()
child = unit()
u.link(child)
```

-------------------------------
## Updating global placement
Updates the object's global placement from its local placement and its parent's global placement.
`view` redraws a displayed object at its new placement.
`deep` applies the update recursively to descendants.

Signature:
```python
u.location_update(deep=True, view=True)
```

-----------------------------------------
## Changing local placement
Sets the local placement to `location` and calls `location_update` with the `deep` and `view` options.

Signature:
```python
u.relocate(location, deep=False, view=True)
```

----------------------
## Displaying in a scene

Signature:
```python
u.bind_to_scene(scene)
```
Adds the unit and its descendants to `scene`. In an ordinary script, `display(u)` handles the scene binding. Set colors when adding geometry with `u.add(obj, color=...)`.

## Assembly example

Both parts are in the coordinate system of `base`. Moving the parent moves them together while preserving their relative placement:

```python
from zencad import *
from zencad.assemble import unit

base = unit()
base.add(box(20, 10, 3), color=blue)
post = unit(parent=base, location=translate(10, 5, 3))
post.add(cylinder(2, 12), color=yellow)
base.relocate(translate(30, 0, 0), deep=True)

assert tuple(post.global_location.translation()) == (40, 5, 3)
display(base)
show()
```
