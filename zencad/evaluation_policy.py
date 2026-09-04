"""Process-wide evaluation timing for ZenCad scripts."""

from evalcache import EvaluationMode

from zencad.operation import resolve_context


_default_mode = EvaluationMode.DEFERRED


def set_evaluation_mode(mode: EvaluationMode | str) -> None:
    """Set evaluation timing in the script header or before running a script.

    Update the existing evaluator so handles, cache contents, progress hooks,
    and runner graph recording keep their ownership. This does not evaluate
    already-created expressions until a subsequent operation needs them.
    """

    global _default_mode
    resolved_mode = EvaluationMode(mode)
    resolve_context()._evaluator.mode = resolved_mode
    _default_mode = resolved_mode


def evaluation_mode() -> EvaluationMode:
    """Return the evaluation mode selected for this script."""

    return resolve_context().mode


__all__ = ["EvaluationMode", "evaluation_mode", "set_evaluation_mode"]
