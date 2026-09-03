"""Public, nestable evaluation-policy contexts for ZenCad operations."""

from contextlib import contextmanager
from typing import Iterator

from evalcache import EvaluationMode

from zencad.geom.context import Context
from zencad.operation import resolve_context, using_context


def _cache_enabled(value, inherited):
    if value is None:
        return inherited
    if not isinstance(value, bool):
        raise TypeError("cache must be a boolean or None")
    return value


@contextmanager
def evaluation(
    mode: EvaluationMode | str,
    *,
    cache: bool | None = None,
) -> Iterator[Context]:
    """Temporarily select evaluation timing and disk-cache policy.

    A fresh context prevents expressions created under different policies from
    being mixed accidentally. Nested uses restore the exact outer context.
    When ``cache`` is omitted, the outer context's policy and store are reused.
    """

    outer = resolve_context()
    resolved_mode = EvaluationMode(mode)
    enabled = _cache_enabled(cache, outer.cache_enabled)
    cache_store = (
        outer._evaluator.cache_store if enabled and outer.cache_enabled else None
    )
    context = Context(
        mode=resolved_mode,
        cache=enabled,
        cache_store=cache_store,
        progress_hooks=outer._evaluator.progress_hooks,
    )
    with using_context(context):
        yield context


def immediate(*, cache: bool | None = None):
    """Return an immediate-evaluation context manager."""

    return evaluation(EvaluationMode.IMMEDIATE, cache=cache)


def eager(*, cache: bool | None = None):
    """Alias for :func:`immediate`, analogous to the former onplace mode."""

    return immediate(cache=cache)


def deferred(*, cache: bool | None = None):
    """Return a deferred-evaluation context manager."""

    return evaluation(EvaluationMode.DEFERRED, cache=cache)


def evaluation_mode() -> EvaluationMode:
    """Return the mode of the currently selected ZenCad context."""

    return resolve_context().mode


__all__ = [
    "EvaluationMode",
    "deferred",
    "eager",
    "evaluation",
    "evaluation_mode",
    "immediate",
]
