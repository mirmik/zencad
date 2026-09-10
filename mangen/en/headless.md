# Automation without the editor

`inspect` and `check` need only the geometry installation. Scripts must declare a static scene with `display()` and `show()`, as in [your first model](helloworld.html). Model code runs in an isolated process.

## inspect — get information about a model

`inspect` runs a script and produces a report about the resulting scene. Use it to find out what the model contains and measure its geometry without opening the editor. Read the report in the terminal or pass JSON to another program. For example, it can report a part's volume and overall dimensions before export.

### Geometry report

```sh
zencad inspect model.py
zencad inspect model.py --json
zencad inspect model.py --output report.json
```

Reports contain object IDs and names, placement, bounding boxes, topology types/counts, area/volume, mesh statistics, digests and validity. Model stdout/stderr is forwarded to command stderr, keeping JSON stdout suitable for pipelines.

### Computation graph

The graph helps explain which operations build a model, which results come from the cache, and where an evaluation failed.

```sh
zencad inspect model.py --tree --no-cache
zencad inspect model.py --graph-json graph.json
zencad inspect model.py --tree --failed-path
```

Trees show operations, shared dependencies, cache/evaluation state and source locations. `--root`, `--max-depth`, `--hide-literals` and `--max-graph-nodes` bound the view. If the output encoding cannot represent tree branches, the CLI uses ASCII; API `to_tree()` retains Unicode. `--graph-json` is a separate graph format, not the geometry report.

See the [inspect reference](../development/headless-inspect.md) for parameters and report formats.

## check — verify model requirements

`check` runs a script and tests the resulting geometry against specified requirements: for example, whether a shape is valid, whether it is a solid, and whether its volume and dimensions fall within acceptable limits. Use it to check model changes automatically from scripts, CI, or an agent. The result is success or a list of failed requirements.

```sh
zencad check model.py --valid --solid
zencad check model.py --volume 700:800 --bbox-size 19:21,9:11,3:5 --json
```

`--valid` checks geometry validity. `--volume 700:800` specifies an acceptable volume range; `--bbox-size 19:21,9:11,3:5` specifies dimension ranges along X, Y, and Z.

`--solid` requires each visible BREP object to have solid type; a compound containing a solid is not itself a solid. Checks target the visible result; multiple objects are aggregated according to the command contract. JSON includes expected/actual/tolerance. Exit `7` means an assertion failed after successful model execution; `0` means success. Script errors use `3`, geometry/scene errors `4`, timeouts `5`, output errors `6` and invalid arguments `2`. Details: [check reference](../development/headless-check.md).

## render — create an image of a model

`render` runs a script and saves a PNG image of the resulting scene. Use it to view the result without operating the editor: for example, to attach a preview to a report or examine a part from several sides. The image helps assess appearance; use `check` to test geometry validity and numeric requirements.

```sh
zencad render model.py -o preview.png
zencad render model.py -o views.png --views iso,front,top,right --size 640x480
```

Views are `iso`, `front`, `back`, `left`, `right`, `top`, `bottom`. Size applies to each tile; multiple views form a contact sheet. Rendering uses an orthographic camera and fresh FitAll, independent of saved editor state. Modes are `shaded`, `shaded-with-edges`, `wireframe`; background, axes and margin are configurable.

### Camera angles and antialiasing

For a custom view, specify both `--yaw` and `--pitch` in degrees:

```sh
zencad render model.py -o preview.png --yaw -65 --pitch 12 --msaa 8
```

`yaw` places the camera around the Z axis: 0 looks from +X, 90 from +Y. `pitch` is camera elevation above XY: 0 is horizontal, 90 looks from above, and −90 from below. Pitch must be between −90 and 90. Supply both angles together; they cannot be combined with `--view`/`--views`. The model is fitted automatically, with padding controlled by `--margin`.

`--msaa` controls edge antialiasing: supported sample counts are 0, 2, 4, and 8. The default is 4; 0 disables antialiasing. It also works with named views.

The Python APIs `render_script` and `render_snapshot` take `yaw` and `pitch` **in radians**, and integer `msaa`. For example: `render_script("model.py", "preview.png", yaw=deg(-65), pitch=deg(12), msaa=8)`, with `deg` imported from `zencad`. If neither angles nor `views` are specified, the view is `iso`.

Rendering requires the `gui` extra and working OpenGL. On a Linux server:

```sh
LIBGL_ALWAYS_SOFTWARE=1 xvfb-run -a zencad render model.py -o preview.png
```

Windows/macOS rendering still needs platform acceptance; GitHub-hosted macOS has shown OpenGL context creation failures. This does not prevent headless inspect/check, which need no viewer. [Rendering contract](../development/deterministic-render.md).

## Python API

```python
from zencad import inspect_script

if __name__ == "__main__":
    report = inspect_script("model.py", cache_enabled=False)
    print(report.to_json())
```

Protect the entry point because evaluation starts a child process. `check_script`, `inspect_computation_graph` and `render_script` are also available; see the development references for formats and parameters.
