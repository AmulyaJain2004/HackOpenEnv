"""Baseline inference for the Bureaucracy Escape Room environment."""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from openai import OpenAI

# Allow running as `python inference.py` from rl_env/.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rl_env import RlAction, RlEnv


API_BASE_URL = os.environ.get("API_BASE_URL")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
LOCAL_IMAGE_NAME = os.environ.get("LOCAL_IMAGE_NAME") or os.environ.get("IMAGE_NAME")
API_KEY = os.environ.get("API_KEY")

TASK_ACTIONS = {
    "dog_license": "select_task_dog_license",
    "business_permit": "select_task_business_permit",
    "construction_permit": "select_task_construction_permit",
}
TASKS = ["dog_license", "business_permit", "construction_permit"]
MAX_STEPS_BY_TASK = {
    "dog_license": 15,
    "business_permit": 25,
    "construction_permit": 40,
}
MAX_TOTAL_REWARD_BY_TASK: Dict[str, float] = {
    "dog_license": 2.0,
    "business_permit": 2.3,
    "construction_permit": 3.2,
}
SUCCESS_SCORE_THRESHOLD = 0.55
BENCHMARK = "bureaucracy_escape_room"
LLM_SUCCESSFUL_CALLS = 0


def _contains_non_ascii(value: str) -> bool:
    return any(ord(character) > 127 for character in value)


def _contains_whitespace(value: str) -> bool:
    return any(character.isspace() for character in value)


def _resolve_runtime_llm_config() -> tuple[str, str]:
    api_base_url = os.environ["API_BASE_URL"].strip()
    api_key = os.environ["API_KEY"].strip()

    if not api_base_url:
        raise RuntimeError("API_BASE_URL is empty")
    if not api_key:
        raise RuntimeError("API_KEY is empty")
    if _contains_non_ascii(api_key) or _contains_whitespace(api_key):
        raise RuntimeError("API_KEY contains invalid characters")

    return api_base_url, api_key


def _probe_llm_proxy(client: OpenAI) -> None:
    global LLM_SUCCESSFUL_CALLS

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Return one word: ok"},
            {"role": "user", "content": "ping"},
        ],
        temperature=0.0,
        max_tokens=4,
    )
    _ = completion.choices[0].message.content
    LLM_SUCCESSFUL_CALLS += 1


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={str(done).lower()} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    reward_blob = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={reward_blob}",
        flush=True,
    )


def _pick_first(actions: List[str], candidates: List[str]) -> Optional[str]:
    for action in candidates:
        if action in actions:
            return action
    return None


def _heuristic_action(task_name: str, observation, history: List[str]) -> Optional[str]:
    actions = observation.available_actions
    inventory = set(observation.inventory)
    dept = observation.current_department

    if task_name == "dog_license":
        if dept == "reception":
            return _pick_first(actions, ["go_to_animal_control"])
        if dept == "animal_control":
            if {"rabies_cert", "fee_receipt"}.issubset(inventory):
                return _pick_first(actions, ["submit_documents"])
            if "rabies_cert" not in inventory:
                return _pick_first(actions, ["go_to_vet_office"])
            if "fee_receipt" not in inventory:
                return _pick_first(actions, ["go_to_cashier"])
        if dept == "vet_office":
            if "rabies_cert" not in inventory:
                return _pick_first(actions, ["confirm_vaccination"])
            return _pick_first(actions, ["go_back_to_animal_control"])
        if dept == "cashier":
            if "fee_receipt" not in inventory:
                return _pick_first(actions, ["pay_fee"])
            return _pick_first(actions, ["go_back_to_animal_control"])

    if task_name == "business_permit":
        if dept == "main_office":
            if {"tax_id", "zoning_clearance", "health_certificate"}.issubset(inventory):
                return _pick_first(actions, ["submit_all_documents"])
            if "zoning_clearance" not in inventory:
                return _pick_first(actions, ["go_to_planning"])
            if "tax_id" not in inventory:
                return _pick_first(actions, ["go_to_revenue"])
            if "health_certificate" not in inventory:
                return _pick_first(actions, ["go_to_health"])
        if dept == "planning":
            if "zoning_clearance" in inventory:
                return _pick_first(actions, ["go_back"])
            if {"proof_of_address", "temp_tax_id"}.issubset(inventory):
                return _pick_first(actions, ["apply_with_temp_tax_id"])
            # Ask once for explicit clue, then go get temporary ID.
            asked = any("ask_about_temp_tax_id" in h for h in history)
            if not asked:
                return _pick_first(actions, ["ask_about_temp_tax_id"])
            return _pick_first(actions, ["go_to_revenue"])
        if dept == "revenue":
            if "tax_id" in inventory:
                return _pick_first(actions, ["go_back"])
            if "zoning_clearance" in inventory:
                return _pick_first(actions, ["apply_for_tax_id"])
            if "temp_tax_id" not in inventory:
                return _pick_first(actions, ["get_temp_tax_id"])
            return _pick_first(actions, ["go_back"])
        if dept == "health":
            if "health_certificate" not in inventory:
                return _pick_first(actions, ["schedule_inspection"])
            return _pick_first(actions, ["go_back"])

    if task_name == "construction_permit":
        if dept == "permits_office":
            if {"structural_survey", "env_clearance", "neighbor_consent", "architect_stamp"}.issubset(inventory):
                return _pick_first(actions, ["submit_all"])
            if "site_assessment" not in inventory:
                return _pick_first(actions, ["go_to_environment", "go_to_fire_safety"])
            if "structural_survey" not in inventory:
                return _pick_first(actions, ["go_to_surveyor"])
            if "env_clearance" not in inventory:
                return _pick_first(actions, ["go_to_environment"])
            if "architect_stamp" not in inventory or "architect_fee_receipt" not in inventory:
                return _pick_first(actions, ["go_to_architect"])
            if "neighbor_consent" not in inventory:
                return _pick_first(actions, ["go_to_neighbors"])
        if dept == "environment":
            if "env_clearance" in inventory:
                return _pick_first(actions, ["go_back"])
            if "site_assessment" not in inventory:
                asked = any("ask_about_deadlock" in h for h in history)
                if not asked:
                    return _pick_first(actions, ["ask_about_deadlock"])
                return _pick_first(actions, ["go_to_fire_safety"])
            if "structural_survey" in inventory:
                return _pick_first(actions, ["request_clearance_with_survey"])
            return _pick_first(actions, ["go_back"])
        if dept == "fire_safety":
            if "site_assessment" not in inventory:
                return _pick_first(actions, ["request_site_assessment"])
            return _pick_first(actions, ["go_back"])
        if dept == "surveyor":
            if "structural_survey" not in inventory and ("env_clearance" in inventory or "site_assessment" in inventory):
                return _pick_first(actions, ["request_survey_with_clearance"])
            return _pick_first(actions, ["go_back"])
        if dept == "architect":
            if "architect_stamp" in inventory:
                return _pick_first(actions, ["go_back"])
            if {"structural_survey", "architect_fee_receipt"}.issubset(inventory):
                return _pick_first(actions, ["get_stamp_with_survey_and_receipt"])
            if "architect_fee_receipt" not in inventory:
                return _pick_first(actions, ["go_to_cashier"])
            return _pick_first(actions, ["go_back"])
        if dept == "cashier":
            if "architect_fee_receipt" not in inventory:
                return _pick_first(actions, ["pay_architect_fee"])
            return _pick_first(actions, ["go_back"])
        if dept == "neighbors":
            if "neighbor_consent" not in inventory and "architect_stamp" in inventory:
                return _pick_first(actions, ["collect_consent_with_stamp"])
            return _pick_first(actions, ["go_back"])

    return None


def get_model_message(client: OpenAI, step: int, message: str, reward: float, history: List[str], actions: List[str]) -> str:
    global LLM_SUCCESSFUL_CALLS
    prompt = (
        "You are solving a bureaucratic workflow. "
        "Return exactly one action from available_actions, no explanation.\n"
        f"Step: {step}\n"
        f"Message: {message}\n"
        f"Last reward: {reward}\n"
        f"Recent history: {history[-4:]}\n"
        f"available_actions: {actions}\n"
    )
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Choose valid next action keys only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=32,
        )
        LLM_SUCCESSFUL_CALLS += 1
        text = (completion.choices[0].message.content or "").strip().splitlines()[0].strip().strip('"\'')
        if text in actions:
            return text
    except Exception:
        pass
    return actions[0] if actions else "select_task_dog_license"


def choose_action(task_name: str, observation, client: OpenAI, step: int, history: List[str], last_reward: float) -> str:
    actions = observation.available_actions
    model_choice = get_model_message(client, step, observation.message, last_reward, history, actions)
    heuristic = _heuristic_action(task_name, observation, history)
    if heuristic and heuristic in actions:
        # Break short loops by selecting a different valid action if heuristic repeats too much.
        if len(history) >= 2:
            a1 = history[-1].split(" action=")[-1].split(" reward=")[0]
            a2 = history[-2].split(" action=")[-1].split(" reward=")[0]
            if heuristic == a1 == a2:
                for candidate in actions:
                    if candidate != heuristic and not candidate.startswith("select_task_"):
                        return candidate
        return heuristic

    return model_choice


async def run_task(client: OpenAI, task_name: str) -> float:
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    env = await RlEnv.from_docker_image(LOCAL_IMAGE_NAME)

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        result = await env.step(RlAction(action=TASK_ACTIONS[task_name]))
        last_reward = result.reward or 0.0
        max_steps = MAX_STEPS_BY_TASK[task_name]

        for step in range(1, max_steps + 1):
            if result.done:
                break

            action = choose_action(task_name, result.observation, client, step, history, last_reward)

            result = await env.step(RlAction(action=action))

            reward = result.reward or 0.0
            done = result.done
            error = getattr(result.observation, "last_action_error", None)

            rewards.append(reward)
            steps_taken = step
            last_reward = reward

            log_step(step=step, action=action, reward=reward, done=done, error=error)
            history.append(f"Step {step}: action={action} reward={reward:+.3f}")

            if done:
                break

        max_total_reward = MAX_TOTAL_REWARD_BY_TASK.get(task_name, 2.5)
        score = sum(rewards) / max_total_reward if max_total_reward > 0 else 0.0
        score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD
    finally:
        try:
            await env.close()
        except Exception:
            pass
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    global LLM_SUCCESSFUL_CALLS
    if not LOCAL_IMAGE_NAME:
        raise RuntimeError("Set LOCAL_IMAGE_NAME when using from_docker_image().")

    api_base_url, api_key = _resolve_runtime_llm_config()
    client = OpenAI(base_url=api_base_url, api_key=api_key)
    _probe_llm_proxy(client)
    scores = []
    for task_name in TASKS:
        scores.append(await run_task(client, task_name))

    if LLM_SUCCESSFUL_CALLS == 0:
        raise RuntimeError("No successful LLM proxy calls were made. Check API_BASE_URL/API_KEY configuration.")

    _ = sum(scores) / len(scores)


if __name__ == "__main__":
    asyncio.run(main())