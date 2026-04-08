# HackOpenEnv

OpenEnv hackathon repository for building and validating a real-world RL environment.

## What This Repo Contains

- `rl_env/`: Main submission environment (Bureaucracy Escape Room), inference script, Docker setup, and validation scripts.

## Quick Start

### 1) Install dependencies

From the repo root:

```bash
pip install -r requirements.txt
```

### 2) Move to the environment directory

```bash
cd rl_env
```

### 3) Build local Docker image

```bash
docker build -t rl_env-env:local -f server/Dockerfile .
```

### 4) Set required inference variables

```bash
export API_BASE_URL=https://api.openai.com/v1
export MODEL_NAME=gpt-4o-mini
export HF_TOKEN=<your-token>
export LOCAL_IMAGE_NAME=rl_env-env:local
```

PowerShell:

```powershell
$env:API_BASE_URL = "https://api.openai.com/v1"
$env:MODEL_NAME = "gpt-4o-mini"
$env:HF_TOKEN = "<your-token>"
$env:LOCAL_IMAGE_NAME = "rl_env-env:local"
```

### 5) Run baseline inference

```bash
python inference.py
```

### 6) Run pre-submission validator

```bash
bash ./scripts/validate-submission.sh https://<your-space>.hf.space .
```

PowerShell:

```powershell
.\scripts\validate-submission.ps1 -PingUrl "https://<your-space>.hf.space" -RepoDir "."
```

## Where To Read More

- Detailed environment documentation: `rl_env/README.md`
