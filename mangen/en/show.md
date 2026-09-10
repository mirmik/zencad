# Scenes and display

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
