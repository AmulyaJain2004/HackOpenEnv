---
title: Bureaucracy Escape Room
emoji: "🚀"
colorFrom: yellow
colorTo: blue
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
    - openenv
    - planning
    - real-world
---

## Bureaucracy Escape Room

An OpenEnv-compliant environment where an AI agent navigates a realistic permit workflow: visiting departments, collecting documents, resolving dependency loops, and submitting final paperwork.

This environment is designed for RL training and evaluation with dense step rewards, deterministic grading, and a clear easy/medium/hard task ladder.

## Quick Start

Use the generated OpenEnv client:

```python
from rl_env import RlAction, RlEnv

try:
    rl_envenv = RlEnv.from_docker_image("rl_env-env:latest")

    result = rl_envenv.reset()
    result = rl_envenv.step(RlAction(action="select_task_dog_license"))

    while not result.done:
        action = result.observation.available_actions[0]
        result = rl_envenv.step(RlAction(action=action))
        print(result.observation.message, result.reward)

finally:
    # Always clean up
    rl_envenv.close()
```

## Tasks

1. `dog_license` (easy): linear dependency chain, short horizon.
2. `business_permit` (medium): circular dependency with hidden workaround.
3. `construction_permit` (hard): multi-department dependencies, ordering constraints, substitute requirement.

## Observation Space

- `current_department`: where the agent is currently operating.
- `message`: current clerk feedback and instructions.
- `inventory`: documents already collected.
- `completed_steps`: achieved milestones.
- `available_actions`: valid action keys for the current state.
- `step_number`: current step in episode.
- `hint`: optional hint exposed by specific actions.

## Action Space

- `action`: one of `available_actions`.
- `message` (optional): natural language note.

Includes task selection actions:

- `select_task_dog_license`
- `select_task_business_permit`
- `select_task_construction_permit`

## Reward Design

- Dense per-step rewards for useful progress.
- Step penalty discourages wandering.
- Loop penalty for repeated identical actions.
- Requirement failures yield zero reward.
- Win reward bonus upon permit issuance.

Reward values are normalized to `[0.0, 1.0]`.

## Deterministic Grading

`tasks.py` includes `grade_episode(...)` with a deterministic score in `[0, 1]` based on:

- milestone completion progress
- final permit success
- step efficiency relative to max step budget

## Building the Docker Image

Before using the environment, you need to build the Docker image:

```bash
# From project root
docker build -t rl_env-env:latest -f server/Dockerfile .
```

## Baseline Inference

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export API_KEY=<your-proxy-api-key>
python inference.py
```

The script emits structured logs in `START` / `STEP` / `END` format.

## Baseline Results

Latest baseline run (MODEL_NAME=`gpt-4o-mini`, local image `rl_env-env:local`):

| Task | Difficulty | Steps | Score | Success |
| --- | --- | ---: | ---: | ---: |
| dog_license | easy | 8 | 0.6800 | true |
| business_permit | medium | 15 | 0.7239 | true |
| construction_permit | hard | 21 | 0.6844 | true |

These scores are produced by the tuned hybrid policy in `inference.py` (task-aware planner + LLM fallback) and are reproducible with the same model and environment image.

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --namespace my-org --private
```

The `openenv push` command will:

1. Validate that the directory is an OpenEnv environment (checks for `openenv.yaml`)
2. Prepare a custom build for Hugging Face Docker space (enables web interface)
3. Upload to Hugging Face (ensuring you're logged in)

### Prerequisites

- Authenticate with Hugging Face: The command will prompt for login if not already authenticated

### Options

- `--directory`, `-d`: Directory containing the OpenEnv environment (defaults to current directory)
- `--repo-id`, `-r`: Repository ID in format 'username/repo-name' (defaults to 'username/env-name' from openenv.yaml)
- `--base-image`, `-b`: Base Docker image to use (overrides Dockerfile FROM)
- `--private`: Deploy the space as private (default: public)

### Examples

```bash
# Push to your personal namespace (defaults to username/env-name from openenv.yaml)
openenv push

# Push to a specific repository
openenv push --repo-id my-org/my-env

# Push with a custom base image
openenv push --base-image ghcr.io/meta-pytorch/openenv-base:latest

# Push as a private space
openenv push --private

# Combine options
openenv push --repo-id my-org/my-env --base-image custom-base:latest --private
```

After deployment, your space will be available at:
`https://huggingface.co/spaces/<repo-id>`

The deployed space includes:

- **Web Interface** at `/web` - Interactive UI for exploring the environment
- **API Documentation** at `/docs` - Full OpenAPI/Swagger interface
- **Health Check** at `/health` - Container health monitoring
- **WebSocket** at `/ws` - Persistent session endpoint for low-latency interactions

## Environment Details

### API

- `POST /reset`
- `POST /step`
- `GET /state`
- `GET /health`
- `GET /web`

### OpenEnv Compliance

- Typed `RlAction`, `RlObservation`, and `RlReward` models.
- `step()`, `reset()`, `state()` implemented via OpenEnv server stack.
- `openenv.yaml` manifest with task metadata.
- 3 deterministic tasks with easy/medium/hard progression.

## Advanced Usage

### Connecting to an Existing Server

```python
from rl_env import RlEnv

# Connect to existing server
rl_envenv = RlEnv(base_url="<ENV_HTTP_URL_HERE>")

# Use as normal
result = rl_envenv.reset()
result = rl_envenv.step(RlAction(action="select_task_business_permit"))
```

Note: When connecting to an existing server, `rl_envenv.close()` will NOT stop the server.

### Using the Context Manager

The client supports context manager usage for automatic connection management:

```python
from rl_env import RlAction, RlEnv

# Connect with context manager (auto-connects and closes)
with RlEnv(base_url="http://localhost:8000") as env:
    result = env.reset()
    print(f"Reset at: {result.observation.current_department}")
    # Multiple steps with low latency
    result = env.step(RlAction(action="select_task_dog_license"))
    for _ in range(4):
        if result.done:
            break
        action = result.observation.available_actions[0]
        result = env.step(RlAction(action=action))
        print(f"Step {result.observation.step_number}: {result.observation.message}")
```

The client uses WebSocket connections for:

- **Lower latency**: No HTTP connection overhead per request
- **Persistent session**: Server maintains your environment state
- **Efficient for episodes**: Better for many sequential steps

### Concurrent WebSocket Sessions

The server can run multiple concurrent sessions (set in `server/app.py`).

```python
from rl_env import RlAction, RlEnv
from concurrent.futures import ThreadPoolExecutor

def run_episode(client_id: int):
    with RlEnv(base_url="http://localhost:8000") as env:
        result = env.reset()
        result = env.step(RlAction(action="select_task_dog_license"))
        for _ in range(8):
            if result.done:
                break
            result = env.step(RlAction(action=result.observation.available_actions[0]))
        return client_id, result.reward

# Run 4 episodes concurrently
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(run_episode, range(4)))
```

## Development & Testing

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

## Project Structure

```text
rl_env/
 .dockerignore         # Docker build exclusions
 __init__.py            # Module exports
 README.md              # This file
 openenv.yaml           # OpenEnv manifest
 pyproject.toml         # Project metadata and dependencies
 uv.lock                # Locked dependencies (generated)
 client.py              # RlEnv client
 models.py              # Action/Observation/Reward models
 tasks.py               # Task definitions + deterministic grader
 inference.py           # Baseline runner with structured logs
 server/
     __init__.py        # Server module exports
     rl_env_environment.py  # Core environment logic
     app.py             # FastAPI application (HTTP + WebSocket endpoints)
    Dockerfile         # Container image definition
```
