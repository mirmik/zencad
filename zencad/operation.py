"""ZenCad domain operations built on decorator-first EvalCache."""

from __future__ import annotations

import functools
import inspect
import types
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    ParamSpec,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

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


_CURRENT_CONTEXT: ContextVar[Context | None] = ContextVar(
    "zencad_current_typed_context",
    default=None,
)
_EXECUTION_CONTEXT: ContextVar[Context | None] = ContextVar(
    "zencad_operation_execution_context",
    default=None,
)
_DEFAULT_CONTEXT: Context | None = None


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
    """Select the sole handle context, the active context, or the default."""

    contexts = {handle.context for value in values for handle in _walk_handles(value)}
    active = _CURRENT_CONTEXT.get()
    if active is not None:
        contexts.add(active)
    if len(contexts) > 1:
        raise ValueError("cannot mix handles from different contexts")
    if contexts:
        return next(iter(contexts))

    global _DEFAULT_CONTEXT
    if _DEFAULT_CONTEXT is None:
        from zencad._typed.context import Context

        _DEFAULT_CONTEXT = Context.deferred()
    return _DEFAULT_CONTEXT


def _reset_default_context() -> None:
    """Drop the process default after its cache configuration changes."""

    global _DEFAULT_CONTEXT
    _DEFAULT_CONTEXT = None


@contextmanager
def using_context(context: Context) -> Iterator[Context]:
    """Temporarily select the evaluator context used by domain operations."""

    token = _CURRENT_CONTEXT.set(context)
    try:
        yield context
    finally:
        _CURRENT_CONTEXT.reset(token)


@contextmanager
def _using_execution_context(context: Context) -> Iterator[Context]:
    token = _EXECUTION_CONTEXT.set(context)
    try:
        yield context
    finally:
        _EXECUTION_CONTEXT.reset(token)


def execution_context() -> Context:
    """Return the context currently executing an operation implementation."""

    context = _EXECUTION_CONTEXT.get()
    return context if context is not None else resolve_context()


def _lower(context: Context, value: object) -> object:
    if _is_handle(value):
        handle = cast("Handle[Any]", value)
        if handle.context is not context:
            raise ValueError("cannot mix handles from different contexts")
        return handle._state
    if isinstance(value, list):
        return [_lower(context, item) for item in value]
    if isinstance(value, tuple):
        return tuple(_lower(context, item) for item in value)
    if isinstance(value, dict):
        return {
            _lower(context, key): _lower(context, item) for key, item in value.items()
        }
    if isinstance(value, set):
        return {_lower(context, item) for item in value}
    if isinstance(value, frozenset):
        return frozenset(_lower(context, item) for item in value)
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


def _rehydrate(annotation: object, value: object) -> object:
    """Restore domain handles for an ordinary implementation call."""

    if annotation in (inspect.Parameter.empty, Any, object):
        return value
    origin = get_origin(annotation)
    if origin in (types.UnionType, Union):
        members = get_args(annotation)
        for member in members:
            if member is type(None) and value is None:
                return None
            if _annotation_accepts_literal(member, value):
                return value
        if isinstance(value, (list, tuple, set, frozenset)):
            for member in members:
                if get_origin(member) in (list, tuple, set, frozenset, Sequence):
                    return _rehydrate(member, value)
        for member in members:
            if not (
                isinstance(member, type)
                and getattr(member, "__zencad_handle__", False)
            ):
                continue
            try:
                restored = _rehydrate(member, value)
            except (TypeError, ValueError):
                continue
            return restored
        return value
    if isinstance(annotation, type) and getattr(
        annotation, "__zencad_handle__", False
    ):
        if isinstance(value, annotation):
            return value
        last_error: TypeError | ValueError | None = None
        for candidate in annotation.__mro__:
            if not getattr(candidate, "__zencad_handle__", False):
                continue
            factory = getattr(candidate, "_from_state", None)
            if factory is None:
                continue
            try:
                return factory(execution_context(), value)
            except (TypeError, ValueError) as error:
                last_error = error
        if last_error is not None:
            raise last_error
        raise TypeError(f"{annotation.__name__} cannot restore operation state")
    if origin in (list, tuple, set, frozenset, Sequence):
        item_annotations = get_args(annotation)
        if not isinstance(value, (list, tuple, set, frozenset)):
            raise TypeError("operation sequence argument has invalid resolved state")
        if origin is tuple and len(item_annotations) > 1 and item_annotations[-1] is not Ellipsis:
            if len(item_annotations) != len(value):
                return tuple(value)
            restored_items = tuple(
                _rehydrate(item_annotation, item)
                for item_annotation, item in zip(item_annotations, value)
            )
        else:
            item_annotation = item_annotations[0] if item_annotations else object
            restored_items = tuple(_rehydrate(item_annotation, item) for item in value)
        if origin is list:
            return list(restored_items)
        if origin is set:
            return set(restored_items)
        if origin is frozenset:
            return frozenset(restored_items)
        return restored_items
    return value


def _annotation_accepts_literal(annotation: object, value: object) -> bool:
    origin = get_origin(annotation)
    if origin is not None:
        return False
    if annotation is float:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(annotation, type) and isinstance(value, annotation)


class DomainOperation(Generic[P, ResolvedT, PublicT]):
    """A typed ZenCad adapter around one reusable EvalCache operation."""

    def __init__(
        self,
        function: Callable[P, object],
        *,
        backend: Callable[..., ResolvedT] | None,
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
        self.prepare = function if backend is not None else None
        self.function = function
        resolved_backend = backend if backend is not None else self._execute
        self.backend = evalcache.operation(
            resolved_backend,
            result=result,
            operation_id=operation_id,
            operation_version=operation_version,
            cacheable=cacheable,
        )
        self.returns = returns
        self.select_result = select_result
        self.fold_literals = fold_literals
        self._type_hints: Mapping[str, object] | None = None
        functools.update_wrapper(self, function)
        if isinstance(returns, type):
            self.__annotations__ = dict(getattr(function, "__annotations__", {}))
            self.__annotations__["return"] = returns
            self.__signature__ = inspect.signature(function).replace(
                return_annotation=returns
            )

    def _execute(self, *args: object, **kwargs: object) -> ResolvedT:
        """Run an ordinary implementation and expose its resolved cache value."""

        bound = inspect.signature(self.function).bind(*args, **kwargs)
        if self._type_hints is None:
            self._type_hints = get_type_hints(self.function)
        for name, value in tuple(bound.arguments.items()):
            annotation = self._type_hints.get(name, inspect.Parameter.empty)
            parameter = inspect.signature(self.function).parameters[name]
            if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                bound.arguments[name] = tuple(
                    _rehydrate(annotation, item) for item in cast(tuple[object, ...], value)
                )
            elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
                bound.arguments[name] = {
                    key: _rehydrate(annotation, item)
                    for key, item in cast(Mapping[str, object], value).items()
                }
            else:
                bound.arguments[name] = _rehydrate(annotation, value)
        value = self.function(*bound.args, **bound.kwargs)
        if not _is_handle(value):
            raise TypeError("a ZenCad operation implementation must return a domain handle")
        handle = cast("Handle[Any]", value)
        if isinstance(handle._state, evalcache.Expression):
            raise TypeError("an operation implementation returned a deferred handle")
        return cast(ResolvedT, handle._state)

    def __get__(self, instance: object, owner: type[object]) -> object:
        if instance is None:
            return self
        return functools.partial(self.__call__, instance)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> PublicT:
        if self.prepare is None:
            prepared = OperationArguments(args=tuple(args), kwargs=kwargs)
        else:
            prepared = self.prepare(*args, **kwargs)
            if not isinstance(prepared, OperationArguments):
                raise TypeError("a ZenCad operation preparer must return arguments(...)")
        context = resolve_context(args, kwargs, prepared.args, prepared.kwargs)
        lowered_args = tuple(_lower(context, value) for value in prepared.args)
        lowered_kwargs = {
            name: _lower(context, value) for name, value in prepared.kwargs.items()
        }
        result = (
            self.select_result(args, kwargs)
            if self.select_result is not None
            else self.backend.result
        )
        if self.fold_literals and not _contains_expression(
            (lowered_args, lowered_kwargs)
        ):
            with _using_execution_context(context):
                state = result.validate(
                    self.backend.function(*lowered_args, **lowered_kwargs),
                    self.backend.operation_id or self.backend.__name__,
                )
        else:
            expression = context._evaluator.expression(
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
                and context.mode is evalcache.EvaluationMode.IMMEDIATE
            ):
                state = context._resolve(expression)
            else:
                if context.mode is evalcache.EvaluationMode.IMMEDIATE:
                    context._resolve(expression)
                state = expression
        handle_type = (
            self.returns(args, kwargs)
            if not isinstance(self.returns, type)
            else self.returns
        )
        factory = getattr(handle_type, "_from_state", None)
        if factory is None:
            raise TypeError("ZenCad operation result must provide _from_state")
        return cast(PublicT, factory(context, state))


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


@overload
def operation(
    *,
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
) -> Callable[[Callable[P, PublicT]], Callable[P, PublicT]]: ...


def operation(
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
    """Adapt a configured EvalCache operation to a ZenCad domain handle."""

    if result is None or returns is None:
        raise TypeError(
            "configured zencad.operation requires result and returns"
        )

    def decorate(
        prepare: Callable[P, object],
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
    "execution_context",
    "operation",
    "resolve_context",
    "using_context",
]
