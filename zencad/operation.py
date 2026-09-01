"""ZenCad domain operations built on decorator-first EvalCache."""

from __future__ import annotations

import functools
import inspect
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, ParamSpec, TypeVar, cast, overload

import evalcache

if TYPE_CHECKING:
    from zencad._typed._core import Handle
    from zencad._typed.context import Context


P = ParamSpec("P")
ResolvedT = TypeVar("ResolvedT")
PublicT = TypeVar("PublicT")


@dataclass(frozen=True)
class OperationArguments:
    """Prepared domain arguments for one resolved EvalCache operation."""

    args: tuple[object, ...]
    kwargs: Mapping[str, object]


def arguments(*args: object, **kwargs: object) -> OperationArguments:
    """Return operands prepared by a :func:`operation` declaration."""

    return OperationArguments(args=args, kwargs=kwargs)


_CURRENT_RUNTIME: ContextVar[Context | None] = ContextVar(
    "zencad_current_typed_runtime",
    default=None,
)
_DEFAULT_RUNTIME: Context | None = None


def _is_handle(value: object) -> bool:
    return getattr(value, "__zencad_handle__", False) is True


def _walk_handles(value: object) -> Iterator[Handle[Any]]:
    if _is_handle(value):
        yield cast("Handle[Any]", value)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield from _walk_handles(key)
            yield from _walk_handles(item)
        return
    if isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            yield from _walk_handles(item)


def resolve_context(*values: object) -> Context:
    """Select the sole handle runtime, the active runtime, or the default."""

    runtimes = {handle.runtime for value in values for handle in _walk_handles(value)}
    active = _CURRENT_RUNTIME.get()
    if active is not None:
        runtimes.add(active)
    if len(runtimes) > 1:
        raise ValueError("cannot mix handles from different typed runtimes")
    if runtimes:
        return next(iter(runtimes))

    global _DEFAULT_RUNTIME
    if _DEFAULT_RUNTIME is None:
        from zencad._typed.context import Context

        _DEFAULT_RUNTIME = Context.deferred()
    return _DEFAULT_RUNTIME


@contextmanager
def using_context(context: Context) -> Iterator[Context]:
    """Temporarily select the evaluator context used by domain operations."""

    token = _CURRENT_RUNTIME.set(context)
    try:
        yield context
    finally:
        _CURRENT_RUNTIME.reset(token)


resolve_runtime = resolve_context
using_runtime = using_context


def _lower(runtime: Context, value: object) -> object:
    if _is_handle(value):
        handle = cast("Handle[Any]", value)
        if handle.runtime is not runtime:
            raise ValueError("cannot mix handles from different typed runtimes")
        return handle._state
    if isinstance(value, list):
        return [_lower(runtime, item) for item in value]
    if isinstance(value, tuple):
        return tuple(_lower(runtime, item) for item in value)
    if isinstance(value, dict):
        return {
            _lower(runtime, key): _lower(runtime, item) for key, item in value.items()
        }
    if isinstance(value, set):
        return {_lower(runtime, item) for item in value}
    if isinstance(value, frozenset):
        return frozenset(_lower(runtime, item) for item in value)
    return value


def _contains_expression(value: object) -> bool:
    if isinstance(value, evalcache.Expression):
        return True
    if isinstance(value, Mapping):
        return any(
            _contains_expression(key) or _contains_expression(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_contains_expression(item) for item in value)
    return False


class DomainOperation(Generic[P, ResolvedT, PublicT]):
    """A typed ZenCad adapter around one reusable EvalCache operation."""

    def __init__(
        self,
        prepare: Callable[P, OperationArguments],
        *,
        backend: Callable[..., ResolvedT],
        result: evalcache.ResultSpec[ResolvedT],
        returns: type[PublicT]
        | Callable[[tuple[object, ...], Mapping[str, object]], type[PublicT]],
        select_result: Callable[
            [tuple[object, ...], Mapping[str, object]], evalcache.ResultSpec[ResolvedT]
        ]
        | None,
        operation_id: str | None,
        operation_version: str | None,
        cacheable: bool,
        fold_literals: bool,
    ) -> None:
        self.prepare = prepare
        self.backend = evalcache.operation(
            backend,
            result=result,
            operation_id=operation_id,
            operation_version=operation_version,
            cacheable=cacheable,
        )
        self.returns = returns
        self.select_result = select_result
        self.fold_literals = fold_literals
        functools.update_wrapper(self, prepare)
        if isinstance(returns, type):
            self.__annotations__ = dict(getattr(prepare, "__annotations__", {}))
            self.__annotations__["return"] = returns
            self.__signature__ = inspect.signature(prepare).replace(
                return_annotation=returns
            )

    def __get__(self, instance: object, owner: type[object]) -> object:
        if instance is None:
            return self
        return functools.partial(self.__call__, instance)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> PublicT:
        prepared = self.prepare(*args, **kwargs)
        if not isinstance(prepared, OperationArguments):
            raise TypeError("a ZenCad operation preparer must return arguments(...)")
        runtime = resolve_context(args, kwargs, prepared.args, prepared.kwargs)
        lowered_args = tuple(_lower(runtime, value) for value in prepared.args)
        lowered_kwargs = {
            name: _lower(runtime, value) for name, value in prepared.kwargs.items()
        }
        result = (
            self.select_result(args, kwargs)
            if self.select_result is not None
            else self.backend.result
        )
        if self.fold_literals and not _contains_expression(
            (lowered_args, lowered_kwargs)
        ):
            state = result.validate(
                self.backend.function(*lowered_args, **lowered_kwargs),
                self.backend.operation_id or self.backend.__name__,
            )
        else:
            expression = runtime._evaluator.expression(
                self.backend.function,
                result=result,
                args=lowered_args,
                kwargs=lowered_kwargs,
                operation_id=self.backend.operation_id,
                operation_version=self.backend.operation_version,
                hash_registry=self.backend.hash_registry,
                cacheable=self.backend.cacheable,
            )
            if (
                self.fold_literals
                and runtime.mode is evalcache.EvaluationMode.IMMEDIATE
            ):
                state = runtime._evaluator.evaluate(expression)
            else:
                if runtime.mode is evalcache.EvaluationMode.IMMEDIATE:
                    runtime._evaluator.evaluate(expression)
                state = expression
        handle_type = (
            self.returns(args, kwargs)
            if not isinstance(self.returns, type)
            else self.returns
        )
        factory = getattr(handle_type, "_from_state", None)
        if factory is None:
            raise TypeError("ZenCad operation result must provide _from_state")
        return cast(PublicT, factory(runtime, state))


@overload
def operation(function: Callable[P, Any], /) -> Any: ...


@overload
def operation(
    *,
    backend: Callable[..., ResolvedT],
    result: evalcache.ResultSpec[ResolvedT],
    returns: type[PublicT]
    | Callable[[tuple[object, ...], Mapping[str, object]], type[PublicT]],
    select_result: Callable[
        [tuple[object, ...], Mapping[str, object]], evalcache.ResultSpec[ResolvedT]
    ]
    | None = None,
    operation_id: str | None = None,
    operation_version: str | None = "1",
    cacheable: bool = True,
    fold_literals: bool = False,
) -> Callable[[Callable[P, OperationArguments]], Callable[P, PublicT]]: ...


def operation(
    function: Callable[P, Any] | None = None,
    /,
    *,
    backend: Callable[..., Any] | None = None,
    result: evalcache.ResultSpec[Any] | None = None,
    returns: type[Any]
    | Callable[[tuple[object, ...], Mapping[str, object]], type[Any]]
    | None = None,
    select_result: Callable[
        [tuple[object, ...], Mapping[str, object]], evalcache.ResultSpec[Any]
    ]
    | None = None,
    operation_id: str | None = None,
    operation_version: str | None = "1",
    cacheable: bool = True,
    fold_literals: bool = False,
) -> Any:
    """Declare a typed domain operation or use the legacy bare compatibility form.

    ``@operation`` without configuration deliberately preserves the historical
    dynamic ``@lazy`` contract. Configured declarations adapt an EvalCache
    operation to a stable ZenCad domain handle.
    """

    legacy_form = (
        backend is None
        and result is None
        and returns is None
        and select_result is None
        and operation_id is None
        and operation_version == "1"
        and cacheable
        and not fold_literals
    )
    if legacy_form:
        from zencad.lazifier import lazy

        if function is None:
            return lambda candidate: lazy(candidate)
        return lazy(function)
    if function is not None:
        raise TypeError("configured zencad.operation must be called with parentheses")
    if backend is None or result is None or returns is None:
        raise TypeError(
            "configured zencad.operation requires backend, result, and returns"
        )

    def decorate(
        prepare: Callable[P, OperationArguments],
    ) -> Callable[P, PublicT]:
        adapter: DomainOperation[P, Any, PublicT] = DomainOperation(
            prepare,
            backend=backend,
            result=result,
            returns=returns,
            select_result=select_result,
            operation_id=operation_id,
            operation_version=operation_version,
            cacheable=cacheable,
            fold_literals=fold_literals,
        )
        return cast(Callable[P, PublicT], adapter)

    return decorate


__all__ = [
    "DomainOperation",
    "OperationArguments",
    "arguments",
    "operation",
    "resolve_context",
    "resolve_runtime",
    "using_context",
    "using_runtime",
]
