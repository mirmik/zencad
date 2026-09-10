# Working with an agent

ZenCad lets an agent complete a modeling cycle: edit a Python script, execute it, obtain measurements and errors, check requirements, and prepare an image for review. The model is available as code, and the result as geometry and a structured report. An agent can check dimensions and solid validity without operating an editor with a mouse.

## What an agent can verify

| Task | ZenCad capability | Practical result |
| --- | --- | --- |
| Build and edit a model | Python scripts with parameters and geometry operations | Changes can be read, compared in Git and executed again. |
| Inspect the result | `inspect --json`: object names, bounds, volume, topology and validity | The agent receives measurable properties as well as images. |
| Check requirements | `check`: validity, solid type, volume and bounding dimensions | Reports contain expected and actual values; exit codes support automatic acceptance or rejection. |
| Locate a failure | Computation trees and graph JSON, source locations, `--failed-path` | Dependencies can be traced to the failing operation and its source. |
| Address a particular part | Names in `display(..., name=...)` and geometric selectors | Reports identify model parts, while faces and edges can be selected by their properties. |
| Review appearance | `render` with explicit views and PNG dimensions | Agents and people can review the result without manually adjusting the camera. |

`inspect` and `check` execute scripts in a separate process without Qt or OpenGL. Model output goes to stderr, leaving JSON stdout available for parsing. Commands distinguish script errors, geometry errors, timeouts and unmet requirements.

## A verifiable iteration

Save this plate with a hole as `model.py`:

```python
from zencad import *

plate = box(20, 10, 4)
hole = cylinder(2, 4).translate(10, 5, 0)
body = (plate - hole).solids().only()
display(body, name="plate")
show()
```

An agent can request a report and check explicit requirements:

```sh
zencad inspect model.py --json
zencad check model.py --valid --solid --volume 749:751 --bbox-size 19.99:20.01,9.99:10.01,3.99:4.01 --json
zencad inspect model.py --tree --no-cache
```

The volume is approximately `749.735`, and the bounding dimensions are `20 × 10 × 4`. The check should exit with code `0`. Increasing the hole radius to `3` still produces a valid solid, but the volume check exits with code `7`: the model no longer meets the requirement. This gives the agent feedback for its next edit.

Prepare several views for visual inspection:

```sh
zencad render model.py -o views.png --views iso,front,top --size 640x480
```

Rendering requires the GUI dependencies and working OpenGL. Numeric checks and images complement each other: the correct volume does not prove that a hole is correctly positioned, and a suitable silhouette does not prove geometry validity.

## Diagnosis and repeated iterations

The computation graph retains dependencies between operations. If construction fails, `zencad inspect model.py --tree --failed-path` helps narrow down the cause. Immediate evaluation and disabling disk caching are useful for debugging; caching can reuse stored results during repeated work. These settings are independent; see [Evaluation and caching](caching.html).

[Geometric selectors](selectors.html) express the intent of a selection, such as edge direction or face position, instead of assuming an ordering. [Geometry validation](validation.html) returns structured error details. Neither replaces task requirements: the agent still needs to specify which dimensions, placements and properties count as correct.

Command options, report formats and execution limitations are described in [Automation: inspect, check, render](headless.html).
