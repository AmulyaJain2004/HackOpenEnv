# HackOpenEnv

OpenEnv hackathon submission repository.

## Environment

Primary environment implementation lives in `my_rl_env`.

Domain: customer support ticket triage.

## Included requirements

- real-world simulation (support operations)
- OpenEnv step/reset/state API using typed models
- 3 deterministic tasks (easy to hard)
- shaped rewards with partial progress and penalties
- baseline runner in root `inference.py`
- Dockerized environment for Hugging Face Spaces

## Quick run

```bash
cd my_rl_env
openenv validate .
docker build -t my_rl_env-env:latest -f server/Dockerfile .
```

Then run baseline from repository root:

```bash
set OPENAI_API_KEY=<key>
set API_BASE_URL=https://api.openai.com/v1
set MODEL_NAME=gpt-4o-mini
python inference.py
```
