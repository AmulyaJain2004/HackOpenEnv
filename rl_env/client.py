# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Client for the Bureaucracy Escape Room environment."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import RlAction, RlObservation


class RlEnv(
    EnvClient[RlAction, RlObservation, State]
):
    """
    Client for the Bureaucracy Escape Room environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with RlEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.current_department)
        ...
        ...     result = client.step(RlAction(action="select_task_dog_license"))
        ...     print(result.observation.available_actions)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = RlEnv.from_docker_image("rl_env-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(RlAction(action="select_task_business_permit"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: RlAction) -> Dict:
        """
        Convert RlAction to JSON payload for step message.

        Args:
            action: RlAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[RlObservation]:
        """
        Parse server response into StepResult[RlObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with RlObservation
        """
        obs_data = payload.get("observation", {})
        observation = RlObservation(
            current_department=obs_data.get("current_department", ""),
            message=obs_data.get("message", ""),
            inventory=obs_data.get("inventory", []),
            completed_steps=obs_data.get("completed_steps", []),
            available_actions=obs_data.get("available_actions", []),
            step_number=obs_data.get("step_number", 0),
            hint=obs_data.get("hint"),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
