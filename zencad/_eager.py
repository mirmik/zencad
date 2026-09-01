"""No-op decorators for resolved OCP backend functions.

The historical geometry modules used EvalCache v1 decorators even when their
private underscore functions were called eagerly.  The public domain layer now
owns all evaluation, so backend decorators intentionally preserve plain Python
call semantics and no longer construct LazyObject proxies.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar


FunctionT = TypeVar("FunctionT", bound=Callable[..., Any])


class Eager:
    """Accept legacy decorator spellings and return the function unchanged."""

    def __call__(
        self,
        function: FunctionT | None = None,
        **_options: object,
    ) -> FunctionT | Callable[[FunctionT], FunctionT]:
        if function is None:
            return self._decorate
        return function

    def decorator(
        self,
        function: FunctionT | None = None,
        **_options: object,
    ) -> FunctionT | Callable[[FunctionT], FunctionT]:
        return self(function)

    def file_creator(self, **_options: object) -> Callable[[FunctionT], FunctionT]:
        return self._decorate

    @staticmethod
    def _decorate(function: FunctionT) -> FunctionT:
        return function


eager = Eager()


__all__ = ["Eager", "eager"]
