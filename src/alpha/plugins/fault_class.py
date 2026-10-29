"""
Fault Class Plugins for Alpha.

Defines pluggable fault implementations across Perception, Actuation, Kinematics,
and Planning boundaries, allowing custom faults to be registered and evaluated.
"""

from __future__ import annotations

import abc
from typing import Any

from alpha.core.entities import FaultType


class FaultPlugin(abc.ABC):
    """Abstract base class for all chaos fault plugins."""

    @property
    @abc.abstractmethod
    def fault_type(self) -> FaultType:
        """The FaultType enum identifier."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def boundary(self) -> str:
        """Boundary layer (Perception, Actuation, Kinematics, Planning)."""
        raise NotImplementedError

    @abc.abstractmethod
    def apply(self, target: Any, intensity: Any, rng: Any) -> Any:
        """Apply the fault to the target object."""
        raise NotImplementedError


class FaultRegistry:
    """Registry for discovering and loading fault plugins."""
    _registry: dict[str, type[FaultPlugin]] = {}

    @classmethod
    def register(cls, name: str, plugin_cls: type[FaultPlugin]) -> None:
        cls._registry[name] = plugin_cls

    @classmethod
    def get(cls, name: str) -> type[FaultPlugin] | None:
        return cls._registry.get(name)

    @classmethod
    def list_faults(cls) -> list[str]:
        return list(cls._registry.keys())

