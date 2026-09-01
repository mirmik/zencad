"""Structured OCCT shape validation and explicit repair operations."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from collections.abc import Iterable, Iterator

import evalcache
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Shape
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.TopAbs import (
    TopAbs_COMPOUND,
    TopAbs_COMPSOLID,
    TopAbs_EDGE,
    TopAbs_FACE,
    TopAbs_SHAPE,
    TopAbs_SHELL,
    TopAbs_SOLID,
    TopAbs_VERTEX,
    TopAbs_WIRE,
)
from OCP.TopoDS import TopoDS_Iterator, TopoDS_Shape

from zencad.geom.shape import Shape, shape_generator
from zencad.lazifier import lazy


_KIND_NAMES = {
    TopAbs_VERTEX: "vertex",
    TopAbs_EDGE: "edge",
    TopAbs_WIRE: "wire",
    TopAbs_FACE: "face",
    TopAbs_SHELL: "shell",
    TopAbs_SOLID: "solid",
    TopAbs_COMPSOLID: "compsolid",
    TopAbs_COMPOUND: "compound",
    TopAbs_SHAPE: "shape",
}


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One machine-readable OCCT status attached to a topology path."""

    code: str
    occt_status: str
    path: str
    shape_type: str
    context_path: str | None = None
    context_type: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "occt_status": self.occt_status,
            "path": self.path,
            "shape_type": self.shape_type,
            "context_path": self.context_path,
            "context_type": self.context_type,
        }


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Versioned validation result suitable for JSON inspection."""

    valid: bool
    shape_type: str
    checked_subshapes: int
    issues: tuple[ValidationIssue, ...]
    exact: bool = False
    parallel: bool = False
    schema_version: int = 1

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "valid": self.valid,
            "shape_type": self.shape_type,
            "checked_subshapes": self.checked_subshapes,
            "exact": self.exact,
            "parallel": self.parallel,
            "issues": [issue.to_dict() for issue in self.issues],
        }


class ShapeValidationError(ValueError):
    """Raised by :func:`assert_valid` with the complete report attached."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        summary = ", ".join(
            f"{issue.code} at {issue.path}" for issue in report.issues[:3]
        )
        if len(report.issues) > 3:
            summary += f", and {len(report.issues) - 3} more"
        super().__init__(
            f"invalid {report.shape_type}: {summary or 'OCCT validation failed'}"
        )


def _kind(shape: TopoDS_Shape) -> str:
    return _KIND_NAMES.get(shape.ShapeType(), "shape")


def _same(left: TopoDS_Shape, right: TopoDS_Shape) -> bool:
    return bool(left.IsSame(right))


def _topology_paths(root: TopoDS_Shape) -> list[tuple[TopoDS_Shape, str]]:
    entries: list[tuple[TopoDS_Shape, str]] = []

    def visit(shape: TopoDS_Shape, path: str) -> None:
        if any(_same(shape, existing) for existing, _ in entries):
            return
        entries.append((shape, path))
        children = TopoDS_Iterator(shape)
        counters: dict[str, int] = {}
        while children.More():
            child = children.Value()
            name = _kind(child)
            index = counters.get(name, 0)
            counters[name] = index + 1
            visit(child, f"{path}/{name}[{index}]")
            children.Next()

    visit(root, _kind(root))
    return entries


def _path_for(
    entries: list[tuple[TopoDS_Shape, str]],
    target: TopoDS_Shape,
) -> str:
    for shape, path in entries:
        if _same(shape, target):
            return path
    return f"{_kind(target)}[unmapped]"


def _status_code(name: str) -> str:
    value = name.removeprefix("BRepCheck_").replace("3D", "3d")
    value = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return re.sub(r"(?<=[a-z])(?=\d)", "_", value)


def _statuses(values: Iterable[object]) -> Iterator[object]:
    yield from values


def _issue(
    status: object,
    shape: TopoDS_Shape,
    path: str,
    context: TopoDS_Shape | None,
    context_path: str | None,
) -> ValidationIssue | None:
    name = getattr(status, "name", str(status))
    if name == "BRepCheck_NoError":
        return None
    return ValidationIssue(
        code=_status_code(name),
        occt_status=name,
        path=path,
        shape_type=_kind(shape),
        context_path=context_path,
        context_type=None if context is None else _kind(context),
    )


def _validate(
    shape: Shape,
    exact: bool = False,
    parallel: bool = False,
) -> ValidationReport:
    if not isinstance(shape, Shape):
        raise TypeError("validate expects a Shape")
    if not isinstance(exact, bool) or not isinstance(parallel, bool):
        raise TypeError("validate exact and parallel options must be bool")
    native = shape.Shape()
    if native.IsNull():
        issue = ValidationIssue(
            code="null_shape",
            occt_status="ZenCad_NullShape",
            path="shape",
            shape_type="shape",
        )
        return ValidationReport(False, "shape", 0, (issue,), exact, parallel)
    entries = _topology_paths(native)
    analyzer = BRepCheck_Analyzer(native)
    analyzer.SetExactMethod(exact)
    analyzer.SetParallel(parallel)
    issues: list[ValidationIssue] = []
    seen: set[tuple[str, str, str | None]] = set()

    for subshape, path in entries:
        result = analyzer.Result(subshape)
        if result is None:
            continue
        for status in _statuses(result.Status()):
            issue = _issue(status, subshape, path, None, None)
            if issue is not None:
                key = (issue.code, issue.path, issue.context_path)
                if key not in seen:
                    seen.add(key)
                    issues.append(issue)

        result.InitContextIterator()
        while result.MoreShapeInContext():
            context = result.ContextualShape()
            context_path = _path_for(entries, context)
            for status in _statuses(result.StatusOnShape(context)):
                issue = _issue(status, subshape, path, context, context_path)
                if issue is not None:
                    key = (issue.code, issue.path, issue.context_path)
                    if key not in seen:
                        seen.add(key)
                        issues.append(issue)
            result.NextShapeInContext()

    valid = bool(analyzer.IsValid()) and not issues
    if not valid and not issues:
        issues.append(
            ValidationIssue(
                code="check_failed",
                occt_status="BRepCheck_CheckFail",
                path=_kind(native),
                shape_type=_kind(native),
            )
        )
    return ValidationReport(
        valid=valid,
        shape_type=_kind(native),
        checked_subshapes=len(entries),
        issues=tuple(issues),
        exact=exact,
        parallel=parallel,
    )


def validate(
    shape: Shape,
    *,
    exact: bool = False,
    parallel: bool = False,
) -> ValidationReport:
    """Materialize ``shape`` and return diagnostics without modifying it."""

    resolved = evalcache.unlazy_if_need(shape)
    return _validate(resolved, exact=exact, parallel=parallel)


def is_valid(
    shape: Shape,
    *,
    exact: bool = False,
    parallel: bool = False,
) -> bool:
    return validate(shape, exact=exact, parallel=parallel).valid


def assert_valid(
    shape: Shape,
    *,
    exact: bool = False,
    parallel: bool = False,
) -> Shape:
    report = validate(shape, exact=exact, parallel=parallel)
    if not report.valid:
        raise ShapeValidationError(report)
    return shape


def _copy(shape: Shape) -> TopoDS_Shape:
    if not isinstance(shape, Shape) or shape.Shape().IsNull():
        raise TypeError("shape repair expects a non-null Shape")
    copied = BRepBuilderAPI_Copy(shape.Shape()).Shape()
    if copied.IsNull():
        raise ValueError("cannot copy Shape for repair")
    return copied


def _clean(shape: Shape) -> Shape:
    """Remove redundant same-domain boundaries from an owned shape copy."""

    algorithm = ShapeUpgrade_UnifySameDomain(_copy(shape), True, True, True)
    algorithm.Build()
    result = algorithm.Shape()
    if result.IsNull():
        raise ValueError("clean produced a null Shape")
    return Shape(result)


@lazy.lazy(cls=shape_generator)
def clean(shape: Shape) -> Shape:
    return _clean(shape)


def _heal(
    shape: Shape,
    tolerance: float = 1e-7,
    max_tolerance: float = 1e-3,
) -> Shape:
    """Run general ShapeFix on an owned copy without asserting success."""

    tolerance = float(tolerance)
    max_tolerance = float(max_tolerance)
    if (
        not math.isfinite(tolerance)
        or not math.isfinite(max_tolerance)
        or tolerance <= 0
        or max_tolerance <= 0
        or tolerance > max_tolerance
    ):
        raise ValueError("heal requires finite 0 < tolerance <= max_tolerance")
    fixer = ShapeFix_Shape(_copy(shape))
    fixer.SetPrecision(tolerance)
    fixer.SetMinTolerance(tolerance)
    fixer.SetMaxTolerance(max_tolerance)
    fixer.Perform()
    result = fixer.Shape()
    if result.IsNull():
        raise ValueError("heal produced a null Shape")
    return Shape(result)


@lazy.lazy(cls=shape_generator)
def heal(
    shape: Shape,
    tolerance: float = 1e-7,
    max_tolerance: float = 1e-3,
) -> Shape:
    return _heal(shape, tolerance, max_tolerance)


__all__ = [
    "ShapeValidationError",
    "ValidationIssue",
    "ValidationReport",
    "assert_valid",
    "clean",
    "heal",
    "is_valid",
    "validate",
]
