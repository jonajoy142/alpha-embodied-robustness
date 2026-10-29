"""
Simulator Adapter Plugin for Alpha.

Provides an extensible abstraction for physics engines (PyBullet, Isaac, MuJoCo).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any

from alpha.clients.simulator_client import PyBulletSimulatorClient
from alpha.core.entities import BlockColor, BlockState, Vec3
from alpha.core.interfaces import SimulatorClient


@dataclass
class SceneRandomizationConfig:
    """Configurable domain randomization for scene generation."""
    enabled: bool = False
    position_jitter_meters: float = 0.02
    friction_min: float = 0.3
    friction_max: float = 1.2
    lateral_friction: float = 0.8


class SimulatorAdapter(SimulatorClient, abc.ABC):
    """Abstract interface for physics simulator backends."""

    @abc.abstractmethod
    def configure_scene_randomization(self, config: SceneRandomizationConfig) -> None:
        """Apply domain randomization settings."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_contact_forces(self) -> list[float]:
        """Return list of current contact normal forces in Newtons."""
        raise NotImplementedError


class PyBulletSimulatorAdapter(SimulatorAdapter):
    """PyBullet implementation of SimulatorAdapter."""

    def __init__(self, inner: PyBulletSimulatorClient | None = None) -> None:
        self._inner = inner or PyBulletSimulatorClient()
        self._randomization = SceneRandomizationConfig()

    def configure_scene_randomization(self, config: SceneRandomizationConfig) -> None:
        self._randomization = config

    def connect(self, gui: bool = False) -> None:
        self._inner.connect(gui=gui)

    def disconnect(self) -> None:
        self._inner.disconnect()

    def build_scene(self) -> dict[str, Any]:
        handles = self._inner.build_scene()
        if self._randomization.enabled:
            self._apply_randomization()
        return handles

    def _apply_randomization(self) -> None:
        try:
            import pybullet as p
            import random
            for color, block_id in getattr(self._inner, "_block_ids", {}).items():
                # Randomize lateral friction
                fric = random.uniform(self._randomization.friction_min, self._randomization.friction_max)
                p.changeDynamics(block_id, -1, lateralFriction=fric)
                # Randomize spawn offset slightly within tabletop bounds
                pos, orn = p.getBasePositionAndOrientation(block_id)
                jitter_x = random.uniform(-self._randomization.position_jitter_meters, self._randomization.position_jitter_meters)
                jitter_y = random.uniform(-self._randomization.position_jitter_meters, self._randomization.position_jitter_meters)
                p.resetBasePositionAndOrientation(block_id, [pos[0] + jitter_x, pos[1] + jitter_y, pos[2]], orn)
        except Exception:
            pass

    def step(self, steps: int = 1) -> None:
        self._inner.step(steps)

    def get_block_state(self, color: BlockColor) -> BlockState:
        return self._inner.get_block_state(color)

    def move_end_effector(self, target_pos: Vec3, target_orn: Any = None) -> dict[str, Any]:
        return self._inner.move_end_effector(target_pos, target_orn)

    def grip(self, color: BlockColor) -> Any:
        return self._inner.grip(color)

    def release(self, grip_handle: Any) -> None:
        self._inner.release(grip_handle)

    def set_block_velocity(self, color: BlockColor, velocity: Vec3) -> None:
        self._inner.set_block_velocity(color, velocity)

    def set_block_position(self, color: BlockColor, pos: Vec3) -> None:
        self._inner.set_block_position(color, pos)

    def get_contact_forces(self) -> list[float]:
        try:
            import pybullet as p
            cps = p.getContactPoints()
            return [float(cp[9]) for cp in cps] if cps else []
        except Exception:
            return []

