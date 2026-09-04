# pythonocc migration baseline

This is the behavioral baseline used to evaluate the migration from
`pythonocc-core` to `cadquery-ocp`. It describes the current implementation;
it is not an installation recommendation.

## Reference environment

- CPython 3.10.19
- pythonocc/OCC 7.6.2
- evalcache 1.15.0
- NumPy 1.26.4
- pytest 8.4.2

The currently published `termin==0.0.0` does not provide the historical
`termin.geombase` API. ZenCad therefore treats its legacy assembly integration
as an optional, lazily imported subsystem; this incompatibility does not alter
the geometry baseline.

## Reproduction

The local reference machine has the legacy binary `OCC` package installed in
its Python environment. A disposable test environment can reuse it as follows:

```bash
python3 -m venv --system-site-packages /tmp/zencad-pythonocc-baseline
mkdir -p /tmp/zencad-baseline-cache
/tmp/zencad-pythonocc-baseline/bin/python - <<'PY'
import pytest
import zencad
import evalcache.dircache_v2

zencad.lazy.cache = evalcache.dircache_v2.DirCache_v2(
    "/tmp/zencad-baseline-cache"
)
raise SystemExit(pytest.main(["-q"]))
PY
```

The explicit cache location keeps the run reproducible in containers and
read-only home directories. It is a test harness setting, not part of the
geometry contract.

## Characterized behavior

`utest/migration_baseline_test.py` records stable, externally observable
properties rather than serialized implementation details:

- analytic mass for a box and sphere;
- topology counts for primitive and boolean results;
- center and bounding box after translation;
- mass and face-count preservation across a BREP round-trip;
- successful non-empty STL export.

Mass and center checks use eight decimal places. Bounding boxes use six
decimal places because OCCT expands their limits by its geometric tolerance.
Topology counts are intentionally exact: a change during the OCP migration
must be reviewed and documented rather than silently accepted.

Reference result:

```text
62 passed
```
