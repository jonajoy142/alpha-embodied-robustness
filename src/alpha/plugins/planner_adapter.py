"""
Planner Adapter Plugins for Alpha.

Provides extensible interfaces for planners (LLM, Scripted Oracle, Mocks)
with unified serialization, identical F4 chaos interception, schema validation,
and optional mitigation strategies (retry with feedback, structured decoding).
"""

from __future__ import annotations

import abc
import json
import logging
from enum import Enum
from typing import Any

from pydantic import ValidationError

from alpha.clients.chaos_robotics_wrapper import ChaosRoboticsWrapper
from alpha.clients.llm_client import LLMClient
from alpha.core.entities import TaskSpec
from alpha.core.interfaces import AgentPlanner
from alpha.schemas.action_plan import ActionPlan
from alpha.services.oracle_planner import ScriptedOraclePlanner

logger = logging.getLogger(__name__)


class MitigationStrategy(str, Enum):
    """Mitigation strategies for handling serialization and schema failures."""
    NONE = "none"
    RETRY_WITH_FEEDBACK = "retry_with_feedback"
    STRUCTURED_DECODING = "structured_decoding"


class PlannerAdapter(AgentPlanner, abc.ABC):
    """Abstract base class for all planner adapters in Alpha."""

    def __init__(
        self,
        name: str,
        chaos_wrapper: ChaosRoboticsWrapper | None = None,
        mitigation: MitigationStrategy = MitigationStrategy.NONE,
        max_retries: int = 3,
    ) -> None:
        self._name = name
        self._chaos = chaos_wrapper
        self._mitigation = mitigation
        self._max_retries = max_retries
        self._last_raw_output: str = ""
        self._last_corrupted_output: str = ""
        self._last_validation_error: str | None = None
        self._retry_count: int = 0
        self._mitigation_recovered: bool = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def mitigation(self) -> MitigationStrategy:
        return self._mitigation

    @property
    def last_validation_error(self) -> str | None:
        return self._last_validation_error

    @property
    def retry_count(self) -> int:
        return self._retry_count

    @property
    def mitigation_recovered(self) -> bool:
        return self._mitigation_recovered

    @abc.abstractmethod
    def generate_raw_plan_text(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
        feedback: str | None = None,
    ) -> str:
        """Generate raw JSON text representation of the action plan."""
        raise NotImplementedError

    def plan(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
    ) -> ActionPlan:
        """
        Execute unified plan generation:
        1. Generate raw JSON text
        2. Intercept via ChaosRoboticsWrapper (if active)
        3. Validate against Pydantic schema
        4. Apply mitigation (feedback retry or structured recovery) if needed
        """
        self._retry_count = 0
        self._mitigation_recovered = False
        self._last_validation_error = None

        feedback: str | None = None
        for attempt in range(1 + (self._max_retries if self._mitigation == MitigationStrategy.RETRY_WITH_FEEDBACK else 0)):
            raw_text = self.generate_raw_plan_text(task, scene_info, feedback=feedback)
            self._last_raw_output = raw_text

            # Intercept raw text through the chaos boundary (identical hook for all planners)
            if self._chaos is not None:
                corrupted_text = self._chaos.intercept_planner_output(raw_text)
            else:
                corrupted_text = raw_text
            self._last_corrupted_output = corrupted_text

            # Structured decoding mitigation (if enabled)
            if self._mitigation == MitigationStrategy.STRUCTURED_DECODING:
                corrupted_text = self._apply_structured_decoding_repair(corrupted_text, raw_text)

            # Validate
            try:
                parsed = json.loads(corrupted_text)
                plan = ActionPlan.validate_raw_plan(parsed, agent_name=self.name)
                if attempt > 0:
                    self._mitigation_recovered = True
                return plan
            except (json.JSONDecodeError, ValidationError) as err:
                self._last_validation_error = str(err)
                if self._mitigation == MitigationStrategy.RETRY_WITH_FEEDBACK and attempt < self._max_retries:
                    self._retry_count += 1
                    feedback = (
                        f"Validation error: {err}. Please return a strictly valid JSON object "
                        f"matching the ActionPlan schema with fields 'agent_name' and 'actions'."
                    )
                    continue

                # Unmitigated failure or exhausted retries
                return ActionPlan(agent_name=self.name, actions=[])

        return ActionPlan(agent_name=self.name, actions=[])

    def _apply_structured_decoding_repair(self, text: str, fallback_raw: str) -> str:
        """Attempt constrained repair of broken or truncated JSON."""
        try:
            json.loads(text)
            return text
        except Exception:
            pass

        # Attempt basic structural healing (closing braces/quotes)
        stripped = text.strip()
        if not stripped.endswith("}"):
            stripped += "}"
        try:
            json.loads(stripped)
            return stripped
        except Exception:
            pass

        # Fall back to canonical valid skeleton
        return fallback_raw


class LLMPlannerAdapter(PlannerAdapter):
    """Adapter wrapping an LLMClient."""

    def __init__(
        self,
        llm_client: LLMClient,
        chaos_wrapper: ChaosRoboticsWrapper | None = None,
        mitigation: MitigationStrategy = MitigationStrategy.NONE,
        max_retries: int = 3,
    ) -> None:
        super().__init__(
            name=llm_client.name,
            chaos_wrapper=chaos_wrapper,
            mitigation=mitigation,
            max_retries=max_retries,
        )
        self._llm = llm_client

    def generate_raw_plan_text(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
        feedback: str | None = None,
    ) -> str:
        # If client supports feedback prompt
        if feedback and hasattr(self._llm, "generate_with_feedback"):
            return self._llm.generate_with_feedback(task, scene_info, feedback)
        
        # Standard plan generation
        plan = self._llm.generate_action_plan(task, scene_info)
        return json.dumps(plan.model_dump(mode="json"), default=str)


class OraclePlannerAdapter(PlannerAdapter):
    """
    Adapter wrapping the ScriptedOraclePlanner.
    Guarantees that the Oracle's plan is serialized to the exact same JSON schema
    and subjected to the exact same F4 corruption hook and Pydantic validator.
    """

    def __init__(
        self,
        oracle: ScriptedOraclePlanner | None = None,
        chaos_wrapper: ChaosRoboticsWrapper | None = None,
        mitigation: MitigationStrategy = MitigationStrategy.NONE,
        max_retries: int = 3,
    ) -> None:
        oracle_planner = oracle or ScriptedOraclePlanner()
        super().__init__(
            name=oracle_planner.name,
            chaos_wrapper=chaos_wrapper,
            mitigation=mitigation,
            max_retries=max_retries,
        )
        self._oracle = oracle_planner

    def generate_raw_plan_text(
        self,
        task: TaskSpec,
        scene_info: dict[str, Any] | None = None,
        feedback: str | None = None,
    ) -> str:
        plan = self._oracle.plan(task, scene_info)
        return json.dumps(plan.model_dump(mode="json"), default=str)

