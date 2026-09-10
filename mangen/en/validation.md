# Geometry validation and repair

```python
import zencad as z

body = z.box(10) + z.box(10).right(10)
report = body.validate()
assert report.valid
print(report.to_dict())
body.assert_valid()
cleaned = body.clean()
healed = cleaned.heal(tolerance=1e-7, max_tolerance=1e-3)
healed.assert_valid()
```

`validate()` materializes the shape and returns a `ValidationReport`: `valid` and structured issues with `code`, `occt_status`, `path`, shape type and optional context. `is_valid()` provides a short answer; `assert_valid()` returns the same shape or raises `ShapeValidationError`.

Validation does not repair geometry. `clean()` removes redundant same-domain boundaries; `heal()` applies tolerance-bounded OCCT healing. Both create a new result without mutating the source. Healing is best-effort: validate its result. `sew()` remains a separate sewing operation.

A valid open shell is not a closed solid. `is_closed()` checks closure only for `Edge` and `Wire`; it does not support `Shell` or `Solid`. Check both validity and solid components for a final body: `zencad check model.py --valid --solid`. [Headless workflow](headless.html), [report format](../development/shape-validation.md).
