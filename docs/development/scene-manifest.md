# Scene object names and manifest

Managed ZenCad scenes expose stable user names and a versioned, payload-free
manifest for agents and build tools. Naming an object does not replace its
run-local `object-000000` ID; it adds a meaningful identity that survives the
snapshot transport and appears in inspection and computation-graph reports.

```python
from zencad import box, cylinder, disp, show

disp(box(20, 10, 4), name="housing")
disp(cylinder(2, 8).up(4), name="shaft")
show()
```

Names are case-sensitive non-empty strings and must be unique within one
scene. Duplicate names fail before the scene is published. Existing unnamed
calls retain their deterministic generated IDs. A single name cannot be
applied to a list or a legacy assembly that expands into several scene
objects; name the individual objects instead.

Every `SceneSnapshot` has a Qt-free `manifest()` method. `SceneDraft` exposes
the same method before publication:

```python
with zencad.managed_scene(1) as scene:
    zencad.disp(zencad.box(2), name="part")
    manifest = scene.manifest({"purpose": "automation"})

print(manifest.to_json())
restored = zencad.SceneManifest.from_dict(manifest.to_dict())
```

The schema is `zencad.scene_manifest`, version 1. Objects remain in scene
order and contain:

- generated `id`, optional user `name`, `kind`, and `visible`;
- presentation properties such as colors, transform, and mesh display mode;
- geometry encoding, byte size, and SHA-256 payload identity.

The manifest never embeds BREP, mesh, OCP, AIS, or Qt objects. Detailed
geometric measurements remain in `zencad inspect`; the manifest is the small
identity and presentation layer shared by inspection, render preflight, and
computation-graph roots.
