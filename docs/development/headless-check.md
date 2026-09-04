# Headless geometry checks

`zencad check` evaluates a model with the same isolated, Qt-free runner as
`zencad inspect`, then applies deterministic assertions to the resulting
geometry report. It is intended for agent loops, CI, and shell scripts that
need a pass/fail contract rather than an image or free-form analysis.

```sh
zencad check model.py --valid --solid
zencad check model.py --kind brep --volume 950:1050
zencad check model.py --area 400:450 \
  --bbox-size 9:11,19:21,4:6 --json
```

With no explicit assertion flags, `check` still requires at least one visible
scene object. Hidden objects remain present in the inspection report but do not
contribute to check measurements.

## Expectations

- `--valid` requires every visible object to report valid geometry. For BREP
  objects, failure details contain the existing versioned `ValidationReport`.
- `--kind brep|mesh|point|line` requires one common scene transport kind.
- `--solid` requires every visible object to be a BREP whose top-level OCCT
  shape type is `solid`.
- `--volume RANGE` checks the sum of all available visible-object volumes.
- `--area RANGE` (also `--surface-area`) checks the sum of all available
  visible-object surface areas.
- `--bbox-size X,Y,Z` checks the size of the union of visible-object world-space
  bounding boxes.
- `--tolerance NUMBER` expands every numeric bound by the same non-negative
  absolute tolerance.

A range is an exact number (`24`), a closed interval (`23.9:24.1`), or an
open-ended interval (`10:` or `:20`). Three bbox ranges are comma-separated.
When a requested measurement is unavailable, that assertion fails with
`actual: null`; it is never silently treated as zero.

Multiple visible objects are aggregated in stable scene order. `volume` and
`surface_area` are sums of the objects that expose those measurements, the
bbox is their spatial union, validity is true only if all objects are valid,
and `solid` is true only if every object is a top-level BREP solid. A mixed set
has `subject.kind: "mixed"` and retains its sorted kinds in `subject.kinds`.

## JSON contract

Reports use `schema: "zencad.check"` and `schema_version: 1`. Consumers must
check both before interpreting the payload. A completed check has status
`"passed"` or `"failed"`, a deterministic `subject` aggregate, a summary, and
an ordered list of assertions. Every assertion contains:

- `name` and `passed`;
- `expected` and `actual`;
- `tolerance` (`null` for non-numeric assertions);
- optional structured `details`.

Model stdout and stderr are forwarded to command stderr. Consequently,
`--json` writes exactly one JSON document to stdout. `--output` atomically
replaces a report file and can be combined with `--json`.

Terminal execution failures use the same schema with `status: "error"` and a
structured `error` object. A failed assertion is not an execution error.

## Exit codes

| Code | Meaning |
| ---: | --- |
| 0 | Every requested assertion passed |
| 2 | Invalid command-line usage |
| 3 | Script failure or unsupported animated scene |
| 4 | Missing scene or geometry that could not be decoded/measured |
| 5 | Script evaluation timed out |
| 6 | The requested report file could not be written |
| 7 | The model completed, but one or more assertions failed |

## Python API

The Python interface accepts typed expectations and does no CLI-string parsing:

```python
from zencad import CheckExpectations, NumericRange, check_script

expectations = CheckExpectations(
    valid=True,
    solid=True,
    volume=NumericRange(950, 1050, tolerance=0.01),
    bbox_size=(
        NumericRange(9, 11),
        NumericRange(19, 21),
        NumericRange(4, 6),
    ),
)
report = check_script("model.py", expectations)
if not report.passed:
    for assertion in report.checks:
        if not assertion.passed:
            print(assertion.name, assertion.expected, assertion.actual)
```

`check_inspection(report, expectations)` applies the same policy to an existing
`InspectionReport`. `check_script` also accepts `timeout`, model `arguments`,
`evaluation_mode`, and `cache_enabled`; for example the CLI spelling
`--eager --no-cache` maps to `evaluation_mode="immediate"` and
`cache_enabled=False`.
