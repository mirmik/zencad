"""Deterministic geometry assertions built on headless inspection reports."""

from collections.abc import Mapping
from dataclasses import dataclass, replace
import math
from numbers import Real
from pathlib import Path
import sys
from typing import Any, Callable

from evalcache import EvaluationMode

from zencad.inspect import (
    GeometryInspectionError,
    InspectionReport,
    _json_text,
    _plain,
    _write_report,
    inspect_script,
)
from zencad.runtime.script_evaluator import (
    AnimatedScriptError,
    MissingSceneError,
    ScriptExecutionError,
    ScriptTimeoutError,
)


CHECK_SCHEMA = "zencad.check"
CHECK_SCHEMA_VERSION = 1
CHECK_FAILED_EXIT_CODE = 7
SCENE_OBJECT_KINDS = ("brep", "mesh", "point", "line")


def _finite_number(value, name) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class NumericRange:
    """Inclusive numeric expectation with an optional absolute tolerance."""

    minimum: float | None = None
    maximum: float | None = None
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        minimum = (
            None if self.minimum is None else _finite_number(self.minimum, "minimum")
        )
        maximum = (
            None if self.maximum is None else _finite_number(self.maximum, "maximum")
        )
        tolerance = _finite_number(self.tolerance, "tolerance")
        if minimum is None and maximum is None:
            raise ValueError("NumericRange requires a minimum or maximum")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("NumericRange minimum must not exceed maximum")
        if tolerance < 0:
            raise ValueError("NumericRange tolerance must be non-negative")
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)
        object.__setattr__(self, "tolerance", tolerance)

    @classmethod
    def exact(cls, value, *, tolerance=0.0) -> "NumericRange":
        value = _finite_number(value, "value")
        return cls(value, value, tolerance)

    def contains(self, value) -> bool:
        if value is None:
            return False
        actual = _finite_number(value, "actual value")
        if self.minimum is not None and actual < self.minimum - self.tolerance:
            return False
        if self.maximum is not None and actual > self.maximum + self.tolerance:
            return False
        return True

    def with_tolerance(self, tolerance) -> "NumericRange":
        return replace(self, tolerance=tolerance)

    def to_dict(self) -> dict[str, float | None]:
        return {"minimum": self.minimum, "maximum": self.maximum}


@dataclass(frozen=True, slots=True)
class CheckExpectations:
    """Typed expectations accepted by :func:`check_script`."""

    non_empty: bool = True
    valid: bool | None = None
    kind: str | None = None
    solid: bool | None = None
    volume: NumericRange | None = None
    surface_area: NumericRange | None = None
    bbox_size: tuple[NumericRange, NumericRange, NumericRange] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.non_empty, bool):
            raise TypeError("non_empty must be a boolean")
        for name in ("valid", "solid"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, bool):
                raise TypeError(f"{name} must be a boolean or None")
        if self.kind is not None and self.kind not in SCENE_OBJECT_KINDS:
            raise ValueError("kind must be one of " + ", ".join(SCENE_OBJECT_KINDS))
        for name in ("volume", "surface_area"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, NumericRange):
                raise TypeError(f"{name} must be a NumericRange or None")
        if self.bbox_size is not None:
            if (
                not isinstance(self.bbox_size, tuple)
                or len(self.bbox_size) != 3
                or not all(isinstance(value, NumericRange) for value in self.bbox_size)
            ):
                raise TypeError(
                    "bbox_size must be a tuple of three NumericRange values"
                )


@dataclass(frozen=True, slots=True)
class CheckSubject:
    """Deterministic aggregate of the visible objects in an inspection report."""

    object_ids: tuple[str, ...]
    total_object_count: int
    kind: str | None
    kinds: tuple[str, ...]
    shape_type: str | None
    shape_types: tuple[str, ...]
    solid: bool
    valid: bool
    volume: float | None
    surface_area: float | None
    bbox_size: tuple[float, float, float] | None

    @property
    def object_count(self) -> int:
        return len(self.object_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_count": self.object_count,
            "total_object_count": self.total_object_count,
            "object_ids": list(self.object_ids),
            "kind": self.kind,
            "kinds": list(self.kinds),
            "shape_type": self.shape_type,
            "shape_types": list(self.shape_types),
            "solid": self.solid,
            "valid": self.valid,
            "volume": self.volume,
            "surface_area": self.surface_area,
            "bbox_size": (None if self.bbox_size is None else list(self.bbox_size)),
        }


@dataclass(frozen=True, slots=True)
class CheckAssertion:
    """One stable expected/actual assertion in a check report."""

    name: str
    passed: bool
    expected: Any
    actual: Any
    tolerance: Any = None
    details: Mapping[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "expected": _plain(self.expected),
            "actual": _plain(self.actual),
            "tolerance": _plain(self.tolerance),
            "details": None if self.details is None else _plain(self.details),
        }


@dataclass(frozen=True, slots=True)
class CheckReport:
    """Versioned result of applying expectations to an inspected scene."""

    subject: CheckSubject
    checks: tuple[CheckAssertion, ...]
    script_path: str | None = None
    schema_version: int = CHECK_SCHEMA_VERSION

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, Any]:
        passed_count = sum(check.passed for check in self.checks)
        return {
            "schema": CHECK_SCHEMA,
            "schema_version": self.schema_version,
            "status": "passed" if self.passed else "failed",
            "script": (
                None if self.script_path is None else {"path": self.script_path}
            ),
            "summary": {
                "check_count": len(self.checks),
                "passed": passed_count,
                "failed": len(self.checks) - passed_count,
            },
            "subject": self.subject.to_dict(),
            "checks": [check.to_dict() for check in self.checks],
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return _json_text(self.to_dict(), indent=indent)


def _common_value(values):
    values = tuple(sorted(set(values)))
    if not values:
        return None, values
    return (values[0] if len(values) == 1 else "mixed"), values


def _aggregate_bbox(objects):
    bounds = [item.geometry.get("bbox") for item in objects]
    bounds = [value for value in bounds if value is not None]
    if not bounds:
        return None
    minimum = tuple(min(value["min"][axis] for value in bounds) for axis in range(3))
    maximum = tuple(max(value["max"][axis] for value in bounds) for axis in range(3))
    return tuple(maximum[axis] - minimum[axis] for axis in range(3))


def _sum_measurement(objects, name):
    values = [item.geometry.get(name) for item in objects]
    values = [float(value) for value in values if value is not None]
    return None if not values else float(sum(values))


def _subject(report: InspectionReport) -> CheckSubject:
    objects = tuple(item for item in report.objects if item.visible)
    kind, kinds = _common_value(item.kind for item in objects)
    shape_type, shape_types = _common_value(
        item.geometry["shape_type"]
        for item in objects
        if item.geometry.get("shape_type") is not None
    )
    return CheckSubject(
        object_ids=tuple(item.object_id for item in objects),
        total_object_count=len(report.objects),
        kind=kind,
        kinds=kinds,
        shape_type=shape_type,
        shape_types=shape_types,
        solid=bool(objects)
        and all(
            item.kind == "brep" and item.geometry.get("shape_type") == "solid"
            for item in objects
        ),
        valid=bool(objects)
        and all(item.geometry.get("valid") is True for item in objects),
        volume=_sum_measurement(objects, "volume"),
        surface_area=_sum_measurement(objects, "surface_area"),
        bbox_size=_aggregate_bbox(objects),
    )


def _range_assertion(name, expected, actual):
    return CheckAssertion(
        name=name,
        passed=expected.contains(actual),
        expected=expected.to_dict(),
        actual=actual,
        tolerance=expected.tolerance,
    )


def _validation_details(report):
    objects = []
    for item in report.objects:
        if not item.visible:
            continue
        validation = item.geometry.get("validation")
        objects.append(
            {
                "id": item.object_id,
                "valid": item.geometry.get("valid") is True,
                "validation": validation,
            }
        )
    return {"objects": objects}


def check_inspection(
    report: InspectionReport,
    expectations: CheckExpectations | None = None,
) -> CheckReport:
    """Apply typed geometry expectations to a headless inspection report."""
    if not isinstance(report, InspectionReport):
        raise TypeError("check_inspection requires an InspectionReport")
    if expectations is None:
        expectations = CheckExpectations()
    if not isinstance(expectations, CheckExpectations):
        raise TypeError("expectations must be CheckExpectations or None")

    subject = _subject(report)
    checks = [
        CheckAssertion(
            "non_empty",
            (subject.object_count > 0) is expectations.non_empty,
            expectations.non_empty,
            subject.object_count > 0,
        )
    ]
    if expectations.valid is not None:
        checks.append(
            CheckAssertion(
                "valid",
                subject.valid is expectations.valid,
                expectations.valid,
                subject.valid,
                details=_validation_details(report),
            )
        )
    if expectations.kind is not None:
        checks.append(
            CheckAssertion(
                "kind",
                subject.kind == expectations.kind,
                expectations.kind,
                subject.kind,
                details={"kinds": list(subject.kinds)},
            )
        )
    if expectations.solid is not None:
        checks.append(
            CheckAssertion(
                "solid",
                subject.solid is expectations.solid,
                expectations.solid,
                subject.solid,
                details={"shape_types": list(subject.shape_types)},
            )
        )
    if expectations.volume is not None:
        checks.append(_range_assertion("volume", expectations.volume, subject.volume))
    if expectations.surface_area is not None:
        checks.append(
            _range_assertion(
                "surface_area", expectations.surface_area, subject.surface_area
            )
        )
    if expectations.bbox_size is not None:
        expected = expectations.bbox_size
        actual = subject.bbox_size
        checks.append(
            CheckAssertion(
                "bbox_size",
                actual is not None
                and all(
                    expectation.contains(actual[axis])
                    for axis, expectation in enumerate(expected)
                ),
                [expectation.to_dict() for expectation in expected],
                None if actual is None else list(actual),
                [expectation.tolerance for expectation in expected],
                details={"axes": ["x", "y", "z"]},
            )
        )

    return CheckReport(
        subject=subject,
        checks=tuple(checks),
        script_path=report.script_path,
    )


def check_script(
    script_path,
    expectations: CheckExpectations | None = None,
    *,
    timeout=30,
    arguments=(),
    evaluation_mode: EvaluationMode | str = EvaluationMode.DEFERRED,
    cache_enabled: bool | None = None,
    output: Callable[[str, str], None] | None = None,
) -> CheckReport:
    """Inspect an isolated model script and apply typed expectations."""
    report = inspect_script(
        script_path,
        timeout=timeout,
        arguments=arguments,
        evaluation_mode=evaluation_mode,
        cache_enabled=cache_enabled,
        output=output,
    )
    return check_inspection(report, expectations)


def _parse_range(value):
    try:
        if ":" not in value:
            return NumericRange.exact(float(value))
        parts = value.split(":")
        if len(parts) != 2 or not any(part.strip() for part in parts):
            raise ValueError
        minimum = float(parts[0]) if parts[0].strip() else None
        maximum = float(parts[1]) if parts[1].strip() else None
        return NumericRange(minimum, maximum)
    except (TypeError, ValueError) as exception:
        import argparse

        raise argparse.ArgumentTypeError(
            "expected NUMBER, MIN:MAX, MIN:, or :MAX"
        ) from exception


def _parse_bbox_size(value):
    import argparse

    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("expected three comma-separated ranges: X,Y,Z")
    return tuple(_parse_range(part) for part in parts)


def _non_negative_finite(value):
    import argparse

    try:
        result = float(value)
    except (TypeError, ValueError) as exception:
        raise argparse.ArgumentTypeError(
            "expected a non-negative number"
        ) from exception
    if not math.isfinite(result) or result < 0:
        raise argparse.ArgumentTypeError("expected a non-negative finite number")
    return result


def _argument_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="zencad check",
        description="Check geometry invariants without opening a GUI.",
    )
    parser.add_argument("script", help="ZenCad Python script")
    parser.add_argument("--valid", action="store_true", help="require valid geometry")
    parser.add_argument(
        "--kind",
        choices=SCENE_OBJECT_KINDS,
        help="require one common scene object kind",
    )
    parser.add_argument(
        "--solid",
        action="store_true",
        help="require every visible object to be a BREP solid",
    )
    parser.add_argument(
        "--volume",
        type=_parse_range,
        metavar="RANGE",
        help="require aggregate volume in NUMBER or MIN:MAX",
    )
    parser.add_argument(
        "--area",
        "--surface-area",
        dest="surface_area",
        type=_parse_range,
        metavar="RANGE",
        help="require aggregate surface area in NUMBER or MIN:MAX",
    )
    parser.add_argument(
        "--bbox-size",
        type=_parse_bbox_size,
        metavar="X,Y,Z",
        help="require aggregate bounding-box size using three ranges",
    )
    parser.add_argument(
        "--tolerance",
        type=_non_negative_finite,
        default=0.0,
        metavar="NUMBER",
        help="absolute tolerance for numeric expectations (default: 0)",
    )
    parser.add_argument(
        "--json", action="store_true", help="write the report to stdout as JSON"
    )
    parser.add_argument(
        "-o", "--output", help="atomically write the JSON report to this file"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30,
        help="script evaluation timeout in seconds (default: 30)",
    )
    evaluation_group = parser.add_mutually_exclusive_group()
    evaluation_group.add_argument(
        "--evaluation",
        choices=tuple(mode.value for mode in EvaluationMode),
        default=EvaluationMode.DEFERRED.value,
        help="evaluation timing policy (default: deferred)",
    )
    evaluation_group.add_argument(
        "--eager",
        dest="evaluation",
        action="store_const",
        const=EvaluationMode.IMMEDIATE.value,
        help="evaluate every operation as it is constructed",
    )
    parser.add_argument(
        "--no-cache",
        dest="cache_enabled",
        action="store_false",
        default=None,
        help="disable cache reads and writes for this run",
    )
    parser.add_argument(
        "script_arguments",
        nargs="*",
        help="arguments passed to the model script (put them after --)",
    )
    return parser


def _with_tolerance(value, tolerance):
    if value is None:
        return None
    if isinstance(value, tuple):
        return tuple(item.with_tolerance(tolerance) for item in value)
    return value.with_tolerance(tolerance)


def _expectations_from_arguments(arguments):
    return CheckExpectations(
        valid=True if arguments.valid else None,
        kind=arguments.kind,
        solid=True if arguments.solid else None,
        volume=_with_tolerance(arguments.volume, arguments.tolerance),
        surface_area=_with_tolerance(arguments.surface_area, arguments.tolerance),
        bbox_size=_with_tolerance(arguments.bbox_size, arguments.tolerance),
    )


def _human_value(value):
    if isinstance(value, (dict, list)):
        return str(value)
    return repr(value)


def _human_report(report):
    lines = [
        f"ZenCad check v{report.schema_version}: {'PASS' if report.passed else 'FAIL'}",
        f"visible objects: {report.subject.object_count}",
    ]
    for check in report.checks:
        lines.append(
            f"{'PASS' if check.passed else 'FAIL'} {check.name}: "
            f"expected {_human_value(check.expected)}, "
            f"actual {_human_value(check.actual)}, "
            f"tolerance {_human_value(check.tolerance)}"
        )
    return "\n".join(lines)


def check_error_report(
    script_path,
    code,
    message,
    *,
    exception_type=None,
    traceback_text=None,
    details=None,
):
    """Build a versioned JSON-ready terminal error report."""
    error = {"code": code, "message": str(message)}
    if exception_type:
        error["exception_type"] = str(exception_type)
    if traceback_text:
        error["traceback"] = str(traceback_text)
    if details:
        error["details"] = _plain(details)
    return {
        "schema": CHECK_SCHEMA,
        "schema_version": CHECK_SCHEMA_VERSION,
        "status": "error",
        "script": {"path": str(Path(script_path).expanduser().resolve())},
        "error": error,
    }


def _emit_cli_report(arguments, payload, *, human=None, error=False):
    text = _json_text(payload)
    if arguments.output:
        _write_report(arguments.output, text)
    if arguments.json:
        sys.stdout.write(text)
    elif not arguments.output and human:
        print(human, file=sys.stderr if error else sys.stdout)


def check_cli(argv=None):
    """Command-line adapter with stable, distinct assertion and error codes."""
    parser = _argument_parser()
    arguments = parser.parse_intermixed_args(argv)

    def script_output(_stream, text):
        sys.stderr.write(text)
        sys.stderr.flush()

    try:
        report = check_script(
            arguments.script,
            _expectations_from_arguments(arguments),
            timeout=arguments.timeout,
            arguments=arguments.script_arguments,
            evaluation_mode=arguments.evaluation,
            cache_enabled=arguments.cache_enabled,
            output=script_output,
        )
        try:
            _emit_cli_report(
                arguments,
                report.to_dict(),
                human=_human_report(report),
            )
        except OSError as exception:
            print(
                f"zencad check: could not write report: {exception}",
                file=sys.stderr,
            )
            return 6
        return 0 if report.passed else CHECK_FAILED_EXIT_CODE
    except ScriptExecutionError as exception:
        error = check_error_report(
            arguments.script,
            "script_error",
            exception.payload.get("message") or str(exception),
            exception_type=exception.payload.get("exception_type"),
            traceback_text=exception.payload.get("traceback"),
            details={"kind": exception.payload.get("kind")},
        )
        exit_code = 3
    except AnimatedScriptError as exception:
        error = check_error_report(arguments.script, "animated_script", str(exception))
        exit_code = 3
    except (MissingSceneError, GeometryInspectionError) as exception:
        details = (
            {"object_id": exception.object_id}
            if isinstance(exception, GeometryInspectionError)
            else None
        )
        error = check_error_report(
            arguments.script,
            "geometry_error" if details else "missing_scene",
            str(exception),
            details=details,
        )
        exit_code = 4
    except ScriptTimeoutError as exception:
        error = check_error_report(
            arguments.script,
            "timeout",
            str(exception),
            details={"timeout_seconds": exception.timeout},
        )
        exit_code = 5
    except (FileNotFoundError, TypeError, ValueError) as exception:
        parser.error(str(exception))

    try:
        _emit_cli_report(
            arguments,
            error,
            human=f"zencad check: {error['error']['message']}",
            error=True,
        )
    except OSError as exception:
        print(f"zencad check: could not write report: {exception}", file=sys.stderr)
        return 6
    return exit_code


__all__ = [
    "CHECK_FAILED_EXIT_CODE",
    "CHECK_SCHEMA",
    "CHECK_SCHEMA_VERSION",
    "CheckAssertion",
    "CheckExpectations",
    "CheckReport",
    "CheckSubject",
    "NumericRange",
    "check_error_report",
    "check_inspection",
    "check_script",
]
