# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Bureaucracy Escape Room OpenEnv environment implementation."""

from copy import deepcopy
from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import RlAction, RlObservation, RlReward
    from ..tasks import check_win_condition, get_task, grade_episode, list_tasks
except ImportError:
    from models import RlAction, RlObservation, RlReward
    from tasks import check_win_condition, get_task, grade_episode, list_tasks


class RlEnvironment(Environment):
    """A real-world bureaucracy simulation with shaped rewards and deterministic grading."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task_id = "dog_license"
        self._task = get_task(self._task_id)
        self._episode: Dict[str, Any] = {}
        self._recent_actions: List[str] = []
        self._last_hint: Optional[str] = None

    def reset(self) -> RlObservation:
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._task_id = "dog_license"
        self._task = get_task(self._task_id)
        self._recent_actions = []
        self._last_hint = None
        self._episode = {
            "task_id": self._task_id,
            "current_department": list(self._task["departments"].keys())[0],
            "inventory": list(self._task.get("starting_inventory", [])),
            "completed_steps": [],
            "step_number": 0,
            "done": False,
            "total_reward": 0.0,
        }
        return self._build_observation(message_override="Environment reset. Task selected: dog_license")

    def step(self, action: RlAction) -> RlObservation:  # type: ignore[override]
        if self._episode.get("done", False):
            reward_obj = RlReward(value=0.0, reason="Episode is already complete.", progress=1.0)
            return self._build_observation(
                message_override="Episode already complete. Call reset() to start a new one.",
                reward_override=reward_obj,
                done_override=True,
                hint_override="Use reset() and then optionally select_task_*.",
            )

        selected_task = self._maybe_switch_task(action.action)
        if selected_task is not None:
            reward_obj = RlReward(value=0.05, reason=f"Switched active task to {selected_task}.", progress=0.0)
            return self._build_observation(
                message_override=f"Task switched to {selected_task}. Episode reset for new task.",
                reward_override=reward_obj,
                done_override=False,
                hint_override="Proceed using available department actions.",
            )

        self._state.step_count += 1
        self._episode["step_number"] += 1

        dept_id = self._episode["current_department"]
        valid_actions = self._get_valid_actions(dept_id)
        action_key = action.action.strip()

        if action_key not in valid_actions:
            reward_obj = RlReward(
                value=0.0,
                reason=f"Invalid action '{action_key}'.",
                progress=self._compute_progress(),
            )
            return self._build_observation(
                message_override="Action rejected.",
                reward_override=reward_obj,
                done_override=False,
                hint_override=f"Valid actions: {sorted(valid_actions.keys())}",
            )

        action_def = valid_actions[action_key]
        missing_requirements = self._missing_requirements(action_def)
        if missing_requirements:
            reward_obj = RlReward(
                value=0.0,
                reason=f"Missing required items: {', '.join(missing_requirements)}",
                progress=self._compute_progress(),
            )
            return self._build_observation(
                message_override="Request rejected by department clerk.",
                reward_override=reward_obj,
                done_override=False,
                hint_override=f"Collect missing items first: {', '.join(missing_requirements)}",
            )

        base_reward = float(action_def.get("reward", 0.0))
        step_penalty = float(self._task.get("step_penalty", 0.01))

        for item in action_def.get("gives", []):
            if item not in self._episode["inventory"]:
                self._episode["inventory"].append(item)

        milestone = action_def.get("completes")
        if milestone and milestone not in self._episode["completed_steps"]:
            self._episode["completed_steps"].append(milestone)

        next_dept = action_def.get("next_dept", dept_id)
        self._episode["current_department"] = next_dept
        self._last_hint = action_def.get("hint")

        loop_penalty = self._loop_penalty(action_key)
        net_reward = max(0.0, base_reward - step_penalty - loop_penalty)

        done = check_win_condition(self._task, self._episode["inventory"])
        if done:
            self._episode["done"] = True
            net_reward = min(1.0, net_reward + float(self._task.get("win_reward", 0.3)))

        if self._episode["step_number"] >= int(self._task.get("max_steps", 30)) and not done:
            self._episode["done"] = True
            done = True
            self._last_hint = "Maximum step budget reached for this task."

        self._episode["total_reward"] += net_reward
        reward_obj = RlReward(
            value=max(0.0, min(1.0, net_reward)),
            reason=action_def.get("message", "Action executed."),
            progress=self._compute_progress(done_override=done),
        )
        return self._build_observation(
            message_override=action_def.get("message", "Action executed."),
            reward_override=reward_obj,
            done_override=done,
            hint_override=self._last_hint,
        )

    @property
    def state(self) -> State:
        return self._state

    def get_state_snapshot(self) -> Dict[str, Any]:
        return {
            "episode_id": self._state.episode_id,
            "step_count": self._state.step_count,
            "task_id": self._task_id,
            "task_name": self._task.get("name"),
            "available_tasks": list_tasks(),
            "episode": deepcopy(self._episode),
            "grader_score": grade_episode(
                self._task_id,
                self._episode.get("completed_steps", []),
                self._episode.get("inventory", []),
                int(self._episode.get("step_number", 0)),
            ),
        }

    def _get_valid_actions(self, dept_id: str) -> Dict[str, Dict[str, Any]]:
        department = self._task["departments"][dept_id]
        actions = dict(department.get("actions", {}))
        actions.update(
            {
                "select_task_dog_license": {"next_dept": "reception", "reward": 0.0, "message": "Task switch action."},
                "select_task_business_permit": {"next_dept": "main_office", "reward": 0.0, "message": "Task switch action."},
                "select_task_construction_permit": {"next_dept": "permits_office", "reward": 0.0, "message": "Task switch action."},
            }
        )
        return actions

    def _maybe_switch_task(self, action_key: str) -> Optional[str]:
        mapping = {
            "select_task_dog_license": "dog_license",
            "select_task_business_permit": "business_permit",
            "select_task_construction_permit": "construction_permit",
        }
        task_id = mapping.get(action_key)
        if task_id is None:
            return None
        self._task_id = task_id
        self._task = get_task(task_id)
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._episode = {
            "task_id": self._task_id,
            "current_department": list(self._task["departments"].keys())[0],
            "inventory": list(self._task.get("starting_inventory", [])),
            "completed_steps": [],
            "step_number": 0,
            "done": False,
            "total_reward": 0.0,
        }
        self._recent_actions = []
        self._last_hint = None
        return task_id

    def _missing_requirements(self, action_def: Dict[str, Any]) -> List[str]:
        inventory = self._episode["inventory"]
        missing: List[str] = []
        substitutions: Dict[str, str] = self._task.get("substitutions", {})
        for req in action_def.get("requires", []):
            substitute = substitutions.get(req)
            if req not in inventory and (substitute is None or substitute not in inventory):
                missing.append(req)
        return missing

    def _compute_progress(self, done_override: bool = False) -> float:
        score = grade_episode(
            self._task_id,
            self._episode.get("completed_steps", []),
            self._episode.get("inventory", []),
            int(self._episode.get("step_number", 0)),
        )
        if done_override and check_win_condition(self._task, self._episode.get("inventory", [])):
            return 1.0
        return max(0.0, min(1.0, score))

    def _loop_penalty(self, action_key: str) -> float:
        self._recent_actions.append(action_key)
        if len(self._recent_actions) > 4:
            self._recent_actions = self._recent_actions[-4:]
        if len(self._recent_actions) >= 3 and len(set(self._recent_actions[-3:])) == 1:
            return 0.05
        return 0.0

    def _build_observation(
        self,
        message_override: Optional[str] = None,
        reward_override: Optional[RlReward] = None,
        done_override: bool = False,
        hint_override: Optional[str] = None,
    ) -> RlObservation:
        dept_id = self._episode["current_department"]
        clerk_intro = self._task["departments"][dept_id]["clerk_intro"]
        available_actions = sorted(self._get_valid_actions(dept_id).keys())
        reward_payload = reward_override or RlReward(value=0.0, reason="Episode initialized.", progress=0.0)

        return RlObservation(
            current_department=dept_id,
            message=message_override or clerk_intro,
            inventory=list(self._episode["inventory"]),
            completed_steps=list(self._episode["completed_steps"]),
            available_actions=available_actions,
            step_number=int(self._episode["step_number"]),
            hint=hint_override,
            done=done_override,
            reward=reward_payload.value,
            metadata={
                "task_id": self._task_id,
                "task_name": self._task.get("name"),
                "reward": reward_payload.model_dump(),
                "grader_score": grade_episode(
                    self._task_id,
                    self._episode.get("completed_steps", []),
                    self._episode.get("inventory", []),
                    int(self._episode.get("step_number", 0)),
                ),
            },
        )
