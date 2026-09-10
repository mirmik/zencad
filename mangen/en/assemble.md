# Hierarchical assemblies.

When displaying a complex or animated scene, it is necessary to work with a large number of connected interactive objects that move relative to each other according to certain laws.

To facilitate this behavior, zencad provides the zencad.assemble library and its main tool zencad.assemble.unit. 

------------------------------------------------------------
## Assembly unit (zencad.assemble.unit).
An assembly unit is an object that has its own local coordinate system, relative to which interactive objects and other units associated with this unit are positioned. Units can create a tree structure by counting their position relative to the position of the parent unit (unit.parent). If the unit does not have an ancestor, its position is measured from the global coordinate system.

The unit contains two coordinate transformation objects - location and global_location.

- location - sets the position of the unit relative to the position of the ancestor unit. location can be updated either directly or using the relocate method.
- global_location is the position of the unit relative to the global coordinate system. global_location is used when rendering an object. global_location is built from the unit.location tree and can be updated using location_update, relocate and other operations. 

------------------
## Adding an object.
Creates and links to the unit an interactive object based on the passed geometry object _obj_.

If an interactive object is passed as a parameter, the unit takes control of it. (Note: the unit controls the location of the interactive object).

Signature: 
```python
u.add(obj, color=None)
```

Пример:
```
m = box(10)
i = box(10).right(20)
u.add(m)
u.add(i)
``` 

--------------------------------
## Adding a child unit.
Sets the _u_ object to be the ancestor of the _child_ object.
Now the position of objects in the unit _child_ (and its descendants) will be calculated taking into account the position of the object _u_. 


Сигнатура:
```python
u.link(child)
```

Пример:
```python
from zencad.assemble import unit

u = unit()
child = unit()
u.link(child)
```

-------------------------------
## Update global position.
Update the global position of the object according to its current position and the global position of the ancestor object.
view - if the object is displayed, redraw it based on the new position.
deep - apply recursively all descendants of an object. 

Сигнатура:
```python
u.location_update(deep=True, view=True)
```

-----------------------------------------
## Update local position.
Change current position to location object and apply location_update procedure with deep, view options.

Сигнатура:
```python
u.relocate(location, deep=False, view=True)
```

----------------------
## Display on stage. 

Сигнатура:
```python
u.bind_to_scene(scene)
```
Add the unit and its descendants to `scene`. Ordinary scripts can call `display(u)` to bind it through the display system. Set colors with `u.add(obj, color=...)`.
