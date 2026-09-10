# Display

## Scene
Scene is a container that stores models and their associated colors.
```python
scene = Scene()
scene.add(model)
scene.add(model, color)
```
`scene.add` returns an interactive_object with which you can change the state of the displayed object (see [interactive_object](interactive_object.html))


---
## zencad.display
A tool for adding geometry to a scene.

```python
zencad.display(shape, color=None, scene=None)
zencad.display(unit, color=None, scene=None, deep=True)
zencad.display(lst, color=None, scene=None)

zencad.disp(model) # alternate
```
Depending on the type of the parameter, display can behave as follows:
For shape - adds to the scene, returns interactive_object
For assemble.unit - calls the bind_to_scene procedure, returns the unit itself
For list, it calls display iteratively on the list items, returns a list of results.

---
## zencad.highlight
A special variant of the display function used to debug the constructed
geometry.
```python
zencad.highlight(model, color=zencad.Color(0.5, 0, 0, 0.5))
zencad.hl(model) # alternate naming
```
Unlike display, the function returns the object passed to it.
Usage example (highlight the subtracted form):
```python
c = a - hl(b.up(100500))
```

## Color
An object containing color information in rgba format. The range of parameter values is [0,1].
```python
Color(r,g,b,a)
```
ZenCad defines a standard set of colors:
```python
zencad.color.white =     zencad.Color(1,1,1)
zencad.color.black =     zencad.Color(0,0,0)
zencad.color.red =       zencad.Color(1,0,0)
zencad.color.green =     zencad.Color(0,1,0)
zencad.color.blue =      zencad.Color(0,0,1)
zencad.color.yellow =    zencad.Color(1,1,0)
zencad.color.magenta =   zencad.Color(1,0,1)
zencad.color.cian =      zencad.Color(0,1,1)
zencad.color.mech =      zencad.Color(0.6, 0.6, 0.8)
zencad.color.transmech = zencad.Color(0.6, 0.6, 0.8, 0.8)
```

## show
```python
zencad.show(scene=None,
			animate=None, preanimate=None, close_handle=None)
```
The show function initiates the display of the renderer program. If the function is called with no arguments, the default scene  is displayed.

show also has a set of parameters to support animation functions for the model (see [Animation](animate.html)).

The show behavior is covered in more detail in ([Internal Kitchen](internal.html))


## Editor scenes and object names

The GUI owns one persistent viewer. A script evaluates in an isolated process
and sends its scene for presentation. Reloading can replace the computation
process while keeping the viewer window. Animated presentation changes travel
separately from the initial geometry.

```python
import zencad as z

part = z.box(10)
controller = z.display(part, name="housing", color=z.Color(0.2, 0.6, 0.8))
z.show()
```

`disp` is shorthand for `display`. It adds an object to the scene; the returned controller manages its presentation. In a managed runner this is a logical `SceneObjectRef`, not a Qt/AIS object. There is no public `zencad.default_scene`: omitting `scene=` uses an internal default. Explicit local scenes use `z.Scene()` and `display(..., scene=scene)`.

A `name=` must be unique within the scene and applies to one object, not a list. Automatic IDs and user names are separate fields. Names appear in inspect and manifests to identify model parts.

`Color(r, g, b, a=0)` accepts components from 0 to 1. The fourth component is transparency: 0 is opaque, 1 transparent. Predefined colors include `z.red`, `z.green`, `z.blue`, `z.yellow`, `z.white` and `z.mech`.

`highlight()`/`hl()` displays a shape and returns that shape, allowing use inside a boolean expression. A display controller and a geometry handle have different roles: [object control](interactive_object.html).

## Named manifest without a GUI

```python
import zencad as z

with z.managed_scene(1) as draft:
    z.display(z.box(2), name="housing")
    manifest = draft.manifest()
    print(manifest.to_json())
```

A manifest contains identity and presentation properties without BREP/mesh payloads. Use [inspect](headless.html) for area, volume and validity, and [managed callbacks](animate.html) for animation.
