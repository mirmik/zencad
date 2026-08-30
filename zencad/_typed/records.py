"""Small typed structured records composed from graph-preserving handles."""

from __future__ import annotations

from collections.abc import Iterator

from ._core import require_same_runtime
from .values import Scalar


class Interval:
    """A named pair of Scalar bounds that keeps both expression states."""

    __slots__ = ("_lower", "_upper")
    __hash__ = None

    def __init__(self, lower: Scalar, upper: Scalar, /) -> None:
        if not isinstance(lower, Scalar) or not isinstance(upper, Scalar):
            raise TypeError("Interval bounds must be Scalar")
        require_same_runtime(lower.runtime, upper)
        self._lower = lower
        self._upper = upper

    @property
    def lower(self) -> Scalar:
        return self._lower

    @property
    def upper(self) -> Scalar:
        return self._upper

    def length(self) -> Scalar:
        return self._upper - self._lower

    def value(self) -> tuple[float, float]:
        """Materialize both bounds as a fixed Python tuple."""
        return (self._lower.value(), self._upper.value())

    def __iter__(self) -> Iterator[Scalar]:
        return iter((self._lower, self._upper))

    def __len__(self) -> int:
        return 2

    def unlazy(self) -> Interval:
        self.value()
        return self
