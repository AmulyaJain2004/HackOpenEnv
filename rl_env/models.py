# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Typed models for the Bureaucracy Escape Room OpenEnv environment."""

from typing import List, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field


class RlAction(Action):
    """Action selected by the agent for the current department."""

    action: str = Field(..., description="Action key chosen from available_actions")
    message: Optional[str] = Field(
        default=None,
        description="Optional natural language note from the agent",
    )


class RlObservation(Observation):
    """Observation returned each step in the bureaucracy simulation."""

    current_department: str = Field(..., description="Current department")
    message: str = Field(..., description="Latest clerk/environment message")
    inventory: List[str] = Field(default_factory=list, description="Documents currently held")
    completed_steps: List[str] = Field(default_factory=list, description="Completed milestones")
    available_actions: List[str] = Field(default_factory=list, description="Valid actions for this step")
    step_number: int = Field(default=0, description="Current step count")
    hint: Optional[str] = Field(default=None, description="Optional guidance surfaced by environment")


class RlReward(BaseModel):
    """Structured reward payload stored in observation metadata."""

    value: float = Field(..., ge=0.0, le=1.0, description="Normalized per-step reward")
    reason: str = Field(..., description="Why this reward was given")
    progress: float = Field(..., ge=0.0, le=1.0, description="Task progress in [0, 1]")
