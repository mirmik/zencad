"""Shared implementation machinery for private typed-domain handles."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, Union

from evalcache import Expression

if TYPE_CHECKING:
    from .context import Context


ResolvedT = TypeVar("ResolvedT")
State = Union[ResolvedT, Expression[ResolvedT]]


class Handle(Generic[ResolvedT]):
    """A stable domain object containing a resolved value or expression."""

    __zencad_handle__ = True
    __slots__ = ("_context", "_state")
    __hash__ = None

    def _bind(self, context: Context, state: State[ResolvedT]) -> None:
        self._context = context
        self._state = state

    @property
    def context(self) -> Context:
        return self._context

    def _resolved(self) -> ResolvedT:
        if isinstance(self._state, Expression):
            return self._context._resolve(self._state)
        return self._state


def require_same_context(context: Context, handle: Handle[ResolvedT]) -> None:
    if handle.context is not context:
        raise ValueError("cannot mix handles from different contexts")
