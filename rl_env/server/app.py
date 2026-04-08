# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Rl Env Environment.

This module creates an HTTP server that exposes the RlEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute an action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from ..models import RlAction, RlObservation
    from .rl_env_environment import RlEnvironment
except (ModuleNotFoundError, ImportError):
    from models import RlAction, RlObservation
    from server.rl_env_environment import RlEnvironment


# Create the app with web interface and README integration
app = create_app(
    RlEnvironment,
    RlAction,
    RlObservation,
    env_name="bureaucracy_escape_room",
    max_concurrent_envs=8,
)


def main():
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m rl_env.server.app

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn rl_env.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
