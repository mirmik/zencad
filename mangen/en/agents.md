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

## Can an agent model in 3D?

Yes. For example:

`antique_column.py`:

```python
#!/usr/bin/env python3
"""A small Ionic-inspired column modelled entirely with ZenCad."""

import math

from zencad import *


def fluted_shaft(
    bottom_radius=21,
    top_radius=18,
    height=122,
    flute_count=20,
    flute_radius=2.25,
):
    """Make a gently tapered shaft with shallow, tapered flutes."""
    shaft = cone(r1=bottom_radius, r2=top_radius, h=height)

    # The cutters follow the taper of the shaft.  Leaving a small uncut band at
    # either end makes the transition into the base and capital more legible.
    cutters = []
    margin = 4
    depth = 0.65
    for index in range(flute_count):
        angle = 2 * math.pi * index / flute_count
        c, s = math.cos(angle), math.sin(angle)

        lower_distance = bottom_radius + flute_radius - depth
        upper_distance = top_radius + flute_radius - depth
        lower = circle(r=flute_radius, wire=True).translate(
            lower_distance * c,
            lower_distance * s,
            margin,
        )
        upper = circle(r=flute_radius, wire=True).translate(
            upper_distance * c,
            upper_distance * s,
            height - margin,
        )
        cutters.append(loft([lower, upper]))

    return shaft - union(cutters)


def ionic_capital(z):
    """Build an abstracted Ionic capital with four visible scroll ends."""
    parts = [
        cylinder(r=19.5, h=4).up(z),
        torus(r1=18.6, r2=2.2).up(z + 4),
        cone(r1=20, r2=27, h=8).up(z + 4),
        box(62, 30, 8, center="xy").up(z + 12),
    ]

    # Two horizontal rolls form the body of the volutes.  Rings placed on both
    # faces give the scrolls a readable stepped profile in the CAD viewer.
    roll_z = z + 16
    for x in (-23, 23):
        parts.append(
            cylinder(r=7.2, h=32, center=True)
            .rotateX(deg(90))
            .translate(x, 0, roll_z)
        )
        for y in (-16.1, 16.1):
            parts.extend(
                [
                    torus(r1=4.8, r2=1.35)
                    .rotateX(deg(90))
                    .translate(x, y, roll_z),
                    cylinder(r=1.8, h=1.2, center=True)
                    .rotateX(deg(90))
                    .translate(x, y, roll_z),
                ]
            )

    parts.extend(
        [
            box(68, 38, 7, center="xy").up(z + 20),
            box(74, 44, 5, center="xy").up(z + 27),
        ]
    )
    return union(parts)


def antique_column():
    """Return the complete 181 mm high column as a single ZenCad shape."""
    base_parts = [
        box(72, 72, 7, center="xy"),
        box(64, 64, 6, center="xy").up(7),
        cylinder(r=30, h=5).up(13),
        torus(r1=26, r2=4).up(18),
        cylinder(r=27, h=4).up(18),
        torus(r1=22.5, r2=3.2).up(23),
        cylinder(r=22, h=4).up(23),
    ]

    shaft_z = 27
    shaft_height = 122
    shaft = fluted_shaft(height=shaft_height).up(shaft_z)

    capital_z = shaft_z + shaft_height
    return union(base_parts + [shaft, ionic_capital(capital_z)])


if __name__ == "__main__":
    marble = Color(0.86, 0.82, 0.70)
    display(antique_column(), color=marble)
    show()
```

![Rendered antique column](../images/antique-column.png)

Command for this view:

```sh
zencad render antique_column.py -o antique-column.png \
  --yaw -65 --pitch 12 --msaa 8 --size 800x1000 \
  --background "#f4f2ed" --timeout 120
```
