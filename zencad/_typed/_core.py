"""Shared implementation machinery for private typed-domain handles."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, Union

from evalcache import Expression

if TYPE_CHECKING:
    from .runtime import Runtime


ResolvedT = TypeVar("ResolvedT")
State = Union[ResolvedT, Expression[ResolvedT]]


class Handle(Generic[ResolvedT]):
    """A stable domain object containing a resolved value or expression."""

    __zencad_handle__ = True
    __slots__ = ("_runtime", "_state")
    __hash__ = None

    def _bind(self, runtime: Runtime, state: State[ResolvedT]) -> None:
        self._runtime = runtime
        self._state = state

    @property
    def runtime(self) -> Runtime:
        return self._runtime

    def _resolved(self) -> ResolvedT:
        if isinstance(self._state, Expression):
            return self._runtime._resolve(self._state)
        return self._state

    def unlazy(self):
        """Materialize for compatibility while preserving the handle object."""
        self._resolved()
        return self


def require_same_runtime(runtime: Runtime, handle: Handle[ResolvedT]) -> None:
    if handle.runtime is not runtime:
        raise ValueError("cannot mix handles from different typed runtimes")
