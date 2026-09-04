"""Evaluator and cache ownership for typed ZenCad domain graphs."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import ParamSpec, TypeVar

from evalcache import (
    CachePolicy,
    CacheStore,
    DirectoryCacheStore,
    EvaluationMode,
    Evaluator,
    Expression,
    ProgressHook,
    ResultSpec,
)

from ._core import State


ResolvedT = TypeVar("ResolvedT")
ContextT = TypeVar("ContextT", bound="Context")
P = ParamSpec("P")


class Context:
    """Own one evaluator and cache policy without exposing a CAD facade."""

    CACHE_NAMESPACE = "zencad-typed-v1"

    def __init__(
        self,
        *,
        mode: EvaluationMode | str = EvaluationMode.DEFERRED,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> None:
        resolved_mode = EvaluationMode(mode)
        if cache:
            policy = CachePolicy(namespace=self.CACHE_NAMESPACE)
            if cache_store is None:
                from zencad.cache_config import current_cache_configuration

                configuration = current_cache_configuration()
                if configuration.enabled:
                    cache_store = DirectoryCacheStore(configuration.directory)
                else:
                    policy = CachePolicy.disabled(namespace=self.CACHE_NAMESPACE)
        else:
            policy = CachePolicy.disabled(namespace=self.CACHE_NAMESPACE)
            cache_store = None
        self._evaluator = Evaluator(
            mode=resolved_mode,
            cache_policy=policy,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @classmethod
    def deferred(
        cls: type[ContextT],
        *,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> ContextT:
        return cls(
            mode=EvaluationMode.DEFERRED,
            cache=cache,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @classmethod
    def immediate(
        cls: type[ContextT],
        *,
        cache: bool = True,
        cache_store: CacheStore | None = None,
        progress_hooks: tuple[ProgressHook, ...] = (),
    ) -> ContextT:
        return cls(
            mode=EvaluationMode.IMMEDIATE,
            cache=cache,
            cache_store=cache_store,
            progress_hooks=progress_hooks,
        )

    @property
    def mode(self) -> EvaluationMode:
        return self._evaluator.mode

    @property
    def cache_enabled(self) -> bool:
        return self._evaluator.cache_policy.enabled

    @property
    def cache_directory(self) -> Path | None:
        """Return the directory used by the built-in disk store, if any."""

        path = getattr(self._evaluator.cache_store, "path", None)
        return None if path is None else Path(path)

    def call(
        self,
        function: Callable[P, ResolvedT],
        /,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> ResolvedT:
        """Call a module-level domain operation in this context."""

        from zencad.operation import resolve_context, using_context

        with using_context(self):
            resolve_context(args, kwargs)
            return function(*args, **kwargs)

    def _expression(
        self,
        operation: Callable[..., ResolvedT],
        *,
        result: ResultSpec[ResolvedT],
        args: tuple[object, ...],
        operation_id: str,
        cacheable: bool = True,
        operation_version: str = "1",
    ) -> Expression[ResolvedT]:
        expression = self._evaluator.expression(
            operation,
            result=result,
            args=args,
            operation_id=operation_id,
            operation_version=operation_version,
            cacheable=cacheable,
        )
        if self.mode is EvaluationMode.IMMEDIATE:
            self._evaluator.evaluate(expression)
        return expression

    def _resolve(self, expression: Expression[ResolvedT]) -> ResolvedT:
        from zencad.operation import _using_execution_context

        with _using_execution_context(self):
            return self._evaluator.evaluate(expression)

    def _value_state(
        self,
        operation: Callable[..., ResolvedT],
        *,
        result: ResultSpec[ResolvedT],
        args: tuple[object, ...],
        operation_id: str,
    ) -> State[ResolvedT]:
        """Fold resolved value operands; otherwise retain an expression."""

        if all(not isinstance(argument, Expression) for argument in args):
            return result.validate(operation(*args), operation_id)
        expression = self._evaluator.expression(
            operation,
            result=result,
            args=args,
            operation_id=operation_id,
            operation_version="1",
        )
        if self.mode is EvaluationMode.IMMEDIATE:
            return self._evaluator.evaluate(expression)
        return expression


__all__ = ["Context"]
