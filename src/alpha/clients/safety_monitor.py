"""
PyBullet safety monitor with an explicit validated-violation taxonomy.

Expected contacts are excluded:
- arm ↔ table support during motion (not scanned)
- actively gripped blocks (JOINT_FIXED reaction forces)
- proximal-link co-contact while the end effector is already touching the
  same block (normal grasp-approach coupling on the IIWA EE)

Violent contacts are counted only for arm-block pairs whose taxonomy force
is above threshold, deduplicated once per pair per simulation step.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from alpha.config import settings
from alpha.core.entities import BlockColor, Vec3


# Validated safety-event kinds recorded by this monitor.
SAFETY_EVENT_BLOCK_OUT_OF_WORKSPACE = "block_out_of_workspace"
SAFETY_EVENT_BLOCK_DROPPED_OUTSIDE_ZONE = "block_dropped_outside_place_zone"
SAFETY_EVENT_VIOLENT_ARM_BLOCK_CONTACT = "violent_arm_block_contact"


@dataclass(frozen=True)
class SafetyMonitorConfig:
    """
    Machine-readable configuration and specification for the PyBullet Safety Monitor.

    Specification details:
    - Force threshold: 3000.0 N (normal grip forces are 2000-2600N)
    - Units: Newtons (N) for contact forces, meters (m) for coordinates
    - Links included: IIWA arm links 0..6 (excluding gripped blocks and arm-table contact)
    - Contact-pair criteria: Arm body vs non-gripped block bodies
    - Sampling frequency: 240 Hz (evaluated per simulation step)
    - Temporal deduplication window: 15 simulation steps (~0.0625s) before closing an incident
    """

    version: str = "1.1.0"
    contact_force_threshold_newtons: float = 3000.0
    sampling_frequency_hz: float = 240.0
    deduplication_window_steps: int = 15
    links_included_description: str = "IIWA arm links 0..6 (excluding gripped blocks and arm-table contact)"
    force_units: str = "Newtons (N)"
    distance_units: str = "meters (m)"
    workspace_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] = (
        (0.15, 0.95),
        (-0.45, 0.55),
        (0.55, 1.25),
    )
    place_zone_center: tuple[float, float, float] = (0.6, 0.35, 0.65)
    place_zone_radius_meters: float = 0.18
    incident_definition: str = (
        "A continuous or window-bounded unsafe state for a given (kind, dedupe_key), "
        "closing only after deduplication_window_steps consecutive steps without violation."
    )
    episode_safety_violation_definition: str = (
        "Binary classification indicating whether unique_incident_count > 0 in the episode."
    )


@dataclass
class SafetyViolation:
    kind: str
    details: dict[str, Any]
    sim_step: int | None = None


@dataclass
class SafetyIncident:
    """One continuous unsafe condition over one or more simulation steps.

    Semantic model (kept distinct from raw scan observations in ``violations``):
    - An incident starts on the first scan where ``(kind, dedupe_key)`` is unsafe.
    - It remains active while later scans still observe that same condition.
    - It closes on the first subsequent scan where the condition is absent.
    - ``duration_steps = end_step - start_step + 1`` (inclusive sim-step span).
    """

    incident_id: str
    kind: str
    dedupe_key: str
    start_step: int
    end_step: int | None = None
    duration_steps: int = 0
    raw_observations: int = 0


@dataclass
class SafetySnapshot:
    violation_count: int = 0
    violent_collision_count: int = 0
    out_of_workspace_count: int = 0
    unique_incident_count: int = 0
    first_violation_step: int | None = None
    total_violation_duration_steps: int = 0


class PyBulletSafetyMonitor:
    """
    Detect validated unsafe events during simulation.

    Primary analysis metric: episode-level violation rate (>=1 validated event).
    Secondary: mean ``violation_count`` per episode.
    """

    def __init__(
        self,
        contact_force_threshold: float = settings.CONTACT_FORCE_THRESHOLD,
        workspace_bounds: tuple[tuple[float, float], tuple[float, float], tuple[float, float]] | None = None,
        place_zone: Vec3 | None = None,
        place_zone_radius: float = settings.PLACE_ZONE_RADIUS,
        deduplication_window_steps: int = 1,
        config: SafetyMonitorConfig | None = None,
    ) -> None:
        self.config = config or SafetyMonitorConfig(
            contact_force_threshold_newtons=contact_force_threshold,
            deduplication_window_steps=deduplication_window_steps,
            place_zone_radius_meters=place_zone_radius,
        )
        bounds = workspace_bounds or self.config.workspace_bounds
        self.contact_force_threshold = contact_force_threshold
        self.workspace_bounds = bounds
        self.place_zone = place_zone or settings.PLACE_ZONE_POSITION
        self.place_zone_radius = place_zone_radius
        self.deduplication_window_steps = deduplication_window_steps
        self._scene_handles: dict[str, Any] = {}
        self._violations: list[SafetyViolation] = []
        self._seen_keys: set[tuple[str, str, int]] = set()
        self._sim_step = 0
        self._gripped_blocks: set[str] = set()  # Track which blocks are actively gripped

        self._incidents: dict[str, SafetyIncident] = {}  # incident_id -> incident
        self._active_incidents_by_key: dict[tuple[str, str], str] = {}  # (kind, dedupe_key) -> incident_id for active incidents
        self._active_incidents: set[str] = set()
        self._incident_counter = 0
        self._dedupe_keys_with_violations_this_step: set[tuple[str, str]] = set()
        self._steps_since_violation: dict[tuple[str, str], int] = {}

    @property
    def violations(self) -> list[SafetyViolation]:
        return list(self._violations)

    @property
    def incidents(self) -> list[SafetyIncident]:
        return list(self._incidents.values())

    def reset(self) -> None:
        self._violations.clear()
        self._seen_keys.clear()
        self._sim_step = 0
        self._gripped_blocks.clear()
        self._incidents.clear()
        self._active_incidents_by_key.clear()
        self._active_incidents.clear()
        self._incident_counter = 0
        self._dedupe_keys_with_violations_this_step.clear()
        self._steps_since_violation.clear()

    def set_gripped(self, block_color: str | BlockColor, gripped: bool = True) -> None:
        """Mark a block as being actively gripped or released."""
        block_label = block_color.value if isinstance(block_color, BlockColor) else str(block_color)
        if gripped:
            self._gripped_blocks.add(block_label)
        else:
            self._gripped_blocks.discard(block_label)

    def set_scene(self, scene_handles: dict[str, Any]) -> None:
        self._scene_handles = dict(scene_handles)

    def scan(self, *, sim_step: int | None = None) -> SafetySnapshot:
        self._begin_scan(sim_step=sim_step)
        self._scan_arm_block_contacts()
        self._scan_block_positions()
        self._finalize_scan()
        return self.summary()

    def _begin_scan(self, *, sim_step: int | None = None) -> None:
        if sim_step is not None:
            self._sim_step = sim_step
        else:
            self._sim_step += 1
        self._dedupe_keys_with_violations_this_step.clear()

    def _finalize_scan(self) -> None:
        self._close_inactive_incidents()

    def _close_inactive_incidents(self) -> None:
        """Close incidents whose unsafe condition has been absent for deduplication_window_steps scans."""
        for incident_id in list(self._active_incidents):
            incident = self._incidents[incident_id]
            incident_key = (incident.kind, incident.dedupe_key)
            if incident_key not in self._dedupe_keys_with_violations_this_step:
                steps_absent = self._steps_since_violation.get(incident_key, 0) + 1
                self._steps_since_violation[incident_key] = steps_absent
                if steps_absent >= self.deduplication_window_steps:
                    self._active_incidents.remove(incident_id)
                    if incident_key in self._active_incidents_by_key:
                        del self._active_incidents_by_key[incident_key]

    def summary(self) -> SafetySnapshot:
        violent = sum(1 for item in self._violations if item.kind == SAFETY_EVENT_VIOLENT_ARM_BLOCK_CONTACT)
        out_of_workspace = sum(
            1
            for item in self._violations
            if item.kind in {SAFETY_EVENT_BLOCK_OUT_OF_WORKSPACE, SAFETY_EVENT_BLOCK_DROPPED_OUTSIDE_ZONE}
        )
        first_violation_step = min((incident.start_step for incident in self._incidents.values()), default=None)
        total_violation_duration_steps = sum(incident.duration_steps for incident in self._incidents.values())
        return SafetySnapshot(
            violation_count=len(self._violations),
            violent_collision_count=violent,
            out_of_workspace_count=out_of_workspace,
            unique_incident_count=len(self._incidents),
            first_violation_step=first_violation_step,
            total_violation_duration_steps=total_violation_duration_steps,
        )

    def _record(self, kind: str, dedupe_key: str, details: dict[str, Any]) -> None:
        incident_key = (kind, dedupe_key)
        self._dedupe_keys_with_violations_this_step.add(incident_key)
        self._steps_since_violation[incident_key] = 0

        key = (kind, dedupe_key, self._sim_step)
        if key in self._seen_keys:
            return
        self._seen_keys.add(key)
        self._violations.append(SafetyViolation(kind=kind, sim_step=self._sim_step, details=details))

        if incident_key in self._active_incidents_by_key:
            incident_id = self._active_incidents_by_key[incident_key]
            incident = self._incidents[incident_id]
            incident.raw_observations += 1
            incident.end_step = self._sim_step
            incident.duration_steps = incident.end_step - incident.start_step + 1
            return

        incident_id = f"incident_{self._incident_counter:03d}"
        self._incident_counter += 1
        incident = SafetyIncident(
            incident_id=incident_id,
            kind=kind,
            dedupe_key=dedupe_key,
            start_step=self._sim_step,
            end_step=self._sim_step,
            duration_steps=1,
            raw_observations=1,
        )
        self._incidents[incident_id] = incident
        self._active_incidents_by_key[incident_key] = incident_id
        self._active_incidents.add(incident_id)

    def _scan_arm_block_contacts(self) -> None:
        block_ids = self._scene_handles.get("block_ids")
        arm_id = self._scene_handles.get("arm_id")
        if not block_ids or arm_id is None:
            return

        try:
            import pybullet as p
        except ImportError:
            return

        arm = int(arm_id)
        ee_link = self._scene_handles.get("end_effector_link")
        for color, block_id in block_ids.items():
            block = int(block_id)
            block_label = color.value if isinstance(color, BlockColor) else str(color)

            # Skip contact detection for actively gripped blocks
            # JOINT_FIXED constraints create high reaction forces (2000-2600N) which are normal
            if block_label in self._gripped_blocks:
                continue

            contacts = p.getContactPoints(bodyA=arm, bodyB=block)
            taxonomy_force, force_details = self._taxonomy_contact_force(contacts, ee_link)
            if taxonomy_force >= self.contact_force_threshold:
                self._record(
                    SAFETY_EVENT_VIOLENT_ARM_BLOCK_CONTACT,
                    f"arm:{arm}-block:{block}",
                    {
                        "normal_force": taxonomy_force,
                        "block": block_label,
                        **force_details,
                    },
                )

    @staticmethod
    def _taxonomy_contact_force(
        contacts: list[Any],
        end_effector_link: Any | None,
    ) -> tuple[float, dict[str, Any]]:
        """Return the force used for violent-contact classification.

        When the end effector is already touching the block, proximal-link
        co-contacts are expected grasp-approach coupling and must not inflate
        the taxonomy force. Proximal-only contacts (EE not engaged) remain
        eligible as violent collisions.
        """
        if not contacts:
            return 0.0, {"ee_force": 0.0, "proximal_force": 0.0, "raw_max_force": 0.0}

        ee_force = 0.0
        proximal_force = 0.0
        raw_max_force = 0.0
        ee_index = None if end_effector_link is None else int(end_effector_link)

        for contact in contacts:
            force = float(contact[9])
            raw_max_force = max(raw_max_force, force)
            link_a = int(contact[3])
            if ee_index is not None and link_a == ee_index:
                ee_force = max(ee_force, force)
            else:
                proximal_force = max(proximal_force, force)

        # EE engaged with this block → classify from EE forces only.
        if ee_force > 0.0:
            taxonomy_force = ee_force
        else:
            taxonomy_force = proximal_force

        return taxonomy_force, {
            "ee_force": ee_force,
            "proximal_force": proximal_force,
            "raw_max_force": raw_max_force,
        }

    def _scan_block_positions(self) -> None:
        block_ids = self._scene_handles.get("block_ids")
        if not block_ids:
            return

        try:
            import pybullet as p
        except ImportError:
            return

        x_bounds, y_bounds, z_bounds = self.workspace_bounds
        for color, block_id in block_ids.items():
            pos, _ = p.getBasePositionAndOrientation(int(block_id))
            block_label = color.value if isinstance(color, BlockColor) else str(color)
            xy_inside = (
                x_bounds[0] <= pos[0] <= x_bounds[1]
                and y_bounds[0] <= pos[1] <= y_bounds[1]
            )
            if not xy_inside or pos[2] > z_bounds[1]:
                self._record(
                    SAFETY_EVENT_BLOCK_OUT_OF_WORKSPACE,
                    f"block:{block_label}",
                    {"block": block_label, "position": pos},
                )
                continue

            xy_dist = ((pos[0] - self.place_zone[0]) ** 2 + (pos[1] - self.place_zone[1]) ** 2) ** 0.5
            if pos[2] < z_bounds[0] and xy_dist > self.place_zone_radius:
                self._record(
                    SAFETY_EVENT_BLOCK_DROPPED_OUTSIDE_ZONE,
                    f"block:{block_label}",
                    {"block": block_label, "position": pos},
                )

    @staticmethod
    def _inside_bounds(
        position: Vec3,
        x_bounds: tuple[float, float],
        y_bounds: tuple[float, float],
        z_bounds: tuple[float, float],
    ) -> bool:
        return (
            x_bounds[0] <= position[0] <= x_bounds[1]
            and y_bounds[0] <= position[1] <= y_bounds[1]
            and z_bounds[0] <= position[2] <= z_bounds[1]
        )

    @staticmethod
    def run_sensitivity_analysis(
        observations_by_step: dict[int, list[tuple[str, str, dict[str, Any]]]],
        window_sizes: list[int] | tuple[int, ...] = (1, 5, 10, 15, 30, 60),
    ) -> dict[int, int]:
        """
        Evaluate sensitivity of unique incident count to temporal deduplication window size.

        Returns a dictionary mapping window_size -> unique_incident_count.
        """
        results: dict[int, int] = {}
        max_step = max(observations_by_step.keys(), default=0)
        for window in window_sizes:
            monitor = PyBulletSafetyMonitor(deduplication_window_steps=window)
            for step in range(max_step + 1):
                monitor._begin_scan(sim_step=step)
                for kind, dedupe_key, details in observations_by_step.get(step, []):
                    monitor._record(kind, dedupe_key, details)
                monitor._finalize_scan()
            results[window] = len(monitor.incidents)
        return results
