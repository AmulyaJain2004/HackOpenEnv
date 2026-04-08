"""Task definitions and deterministic graders for the bureaucracy environment."""

from copy import deepcopy
from typing import Any, Dict, List


TASKS: Dict[str, Dict[str, Any]] = {
    "dog_license": {
        "name": "Dog License",
        "difficulty": "easy",
        "description": "Obtain a dog license by gathering required documents.",
        "max_steps": 15,
        "step_penalty": 0.02,
        "departments": {
            "reception": {
                "clerk_intro": "Welcome to City Hall. For a dog license, visit Animal Control.",
                "actions": {
                    "go_to_animal_control": {
                        "next_dept": "animal_control",
                        "reward": 0.10,
                        "message": "You head to Animal Control.",
                    },
                    "ask_for_form": {
                        "next_dept": "reception",
                        "reward": 0.05,
                        "message": "You get a general info pamphlet.",
                        "gives": ["info_pamphlet"],
                    },
                },
            },
            "animal_control": {
                "clerk_intro": "Need rabies certificate and fee receipt before we issue a dog license.",
                "actions": {
                    "submit_documents": {
                        "requires": ["rabies_cert", "fee_receipt"],
                        "next_dept": "animal_control",
                        "reward": 0.45,
                        "message": "Documents accepted. Dog license issued!",
                        "gives": ["dog_license"],
                        "completes": "submit_final",
                    },
                    "go_to_vet_office": {
                        "next_dept": "vet_office",
                        "reward": 0.08,
                        "message": "You head to the Vet Office.",
                    },
                    "go_to_cashier": {
                        "next_dept": "cashier",
                        "reward": 0.08,
                        "message": "You head to the Cashier.",
                    },
                },
            },
            "vet_office": {
                "clerk_intro": "We can issue rabies certificate after record verification.",
                "actions": {
                    "confirm_vaccination": {
                        "next_dept": "vet_office",
                        "reward": 0.20,
                        "message": "Rabies certificate issued.",
                        "gives": ["rabies_cert"],
                        "completes": "get_rabies_cert",
                    },
                    "go_back_to_animal_control": {
                        "next_dept": "animal_control",
                        "reward": 0.03,
                        "message": "Back to Animal Control.",
                    },
                },
            },
            "cashier": {
                "clerk_intro": "Dog license fee is $20. Ready to pay?",
                "actions": {
                    "pay_fee": {
                        "next_dept": "cashier",
                        "reward": 0.20,
                        "message": "Payment accepted. Fee receipt issued.",
                        "gives": ["fee_receipt"],
                        "completes": "pay_fee",
                    },
                    "go_back_to_animal_control": {
                        "next_dept": "animal_control",
                        "reward": 0.03,
                        "message": "Back to Animal Control.",
                    },
                },
            },
        },
        "milestones": ["get_rabies_cert", "pay_fee", "submit_final"],
        "win_condition": {"inventory_has": ["dog_license"]},
        "win_reward": 0.35,
    },
    "business_permit": {
        "name": "Business Permit",
        "difficulty": "medium",
        "description": "Resolve circular dependencies to obtain a business permit.",
        "max_steps": 25,
        "step_penalty": 0.015,
        "starting_inventory": ["proof_of_address"],
        "departments": {
            "main_office": {
                "clerk_intro": "Need Tax ID, Zoning Clearance, and Health Certificate.",
                "actions": {
                    "submit_all_documents": {
                        "requires": ["tax_id", "zoning_clearance", "health_certificate"],
                        "next_dept": "main_office",
                        "reward": 0.45,
                        "message": "All documents accepted. Business permit issued!",
                        "gives": ["business_permit"],
                        "completes": "submit_final",
                    },
                    "go_to_revenue": {"next_dept": "revenue", "reward": 0.05, "message": "You head to Revenue."},
                    "go_to_planning": {"next_dept": "planning", "reward": 0.05, "message": "You head to Planning."},
                    "go_to_health": {"next_dept": "health", "reward": 0.05, "message": "You head to Health."},
                },
            },
            "revenue": {
                "clerk_intro": "Tax ID requires zoning clearance.",
                "actions": {
                    "apply_for_tax_id": {
                        "requires": ["zoning_clearance"],
                        "next_dept": "revenue",
                        "reward": 0.20,
                        "message": "Tax ID issued.",
                        "gives": ["tax_id"],
                        "completes": "get_tax_id",
                    },
                    "get_temp_tax_id": {
                        "requires": ["proof_of_address"],
                        "next_dept": "revenue",
                        "reward": 0.15,
                        "message": "Temporary Tax ID issued.",
                        "gives": ["temp_tax_id"],
                        "completes": "get_temp_tax_id",
                    },
                    "apply_without_clearance": {
                        "next_dept": "revenue",
                        "reward": -0.05,
                        "message": "Rejected. Zoning clearance required.",
                    },
                    "go_back": {"next_dept": "main_office", "reward": 0.02, "message": "Back to Main Office."},
                },
            },
            "planning": {
                "clerk_intro": "Zoning needs proof of address and tax ID.",
                "actions": {
                    "apply_with_temp_tax_id": {
                        "requires": ["proof_of_address", "temp_tax_id"],
                        "next_dept": "planning",
                        "reward": 0.20,
                        "message": "Zoning clearance issued.",
                        "gives": ["zoning_clearance"],
                        "completes": "get_zoning",
                    },
                    "ask_about_temp_tax_id": {
                        "next_dept": "planning",
                        "reward": 0.10,
                        "message": "Revenue can provide a Temporary Tax ID.",
                        "hint": "Go to Revenue and request get_temp_tax_id.",
                    },
                    "go_to_revenue": {"next_dept": "revenue", "reward": 0.03, "message": "You head to Revenue."},
                    "go_back": {"next_dept": "main_office", "reward": 0.02, "message": "Back to Main Office."},
                },
            },
            "health": {
                "clerk_intro": "Health inspection requires proof of address.",
                "actions": {
                    "schedule_inspection": {
                        "requires": ["proof_of_address"],
                        "next_dept": "health",
                        "reward": 0.18,
                        "message": "Inspection complete. Health certificate issued.",
                        "gives": ["health_certificate"],
                        "completes": "get_health_cert",
                    },
                    "go_back": {"next_dept": "main_office", "reward": 0.02, "message": "Back to Main Office."},
                },
            },
        },
        "milestones": ["get_temp_tax_id", "get_zoning", "get_tax_id", "get_health_cert", "submit_final"],
        "win_condition": {"inventory_has": ["business_permit"]},
        "win_reward": 0.30,
    },
    "construction_permit": {
        "name": "Construction Permit",
        "difficulty": "hard",
        "description": "Solve a multi-department dependency graph with hidden workaround.",
        "max_steps": 40,
        "step_penalty": 0.01,
        "departments": {
            "permits_office": {
                "clerk_intro": "Need structural survey, environmental clearance, neighbor consent, architect stamp.",
                "actions": {
                    "submit_all": {
                        "requires": ["structural_survey", "env_clearance", "neighbor_consent", "architect_stamp"],
                        "next_dept": "permits_office",
                        "reward": 0.45,
                        "message": "All verified. Construction permit issued!",
                        "gives": ["construction_permit"],
                        "completes": "final_submission",
                    },
                    "go_to_surveyor": {"next_dept": "surveyor", "reward": 0.05, "message": "You head to Surveyor."},
                    "go_to_environment": {"next_dept": "environment", "reward": 0.05, "message": "You head to Environment."},
                    "go_to_neighbors": {"next_dept": "neighbors", "reward": 0.05, "message": "You head to Neighbors Liaison."},
                    "go_to_architect": {"next_dept": "architect", "reward": 0.05, "message": "You head to Architect."},
                    "go_to_fire_safety": {"next_dept": "fire_safety", "reward": 0.05, "message": "You head to Fire Safety."},
                },
            },
            "surveyor": {
                "clerk_intro": "Survey requires environmental clearance (or accepted substitute).",
                "actions": {
                    "request_survey_with_clearance": {
                        "requires": ["env_clearance"],
                        "next_dept": "surveyor",
                        "reward": 0.18,
                        "message": "Structural survey issued.",
                        "gives": ["structural_survey"],
                        "completes": "get_survey",
                    },
                    "go_back": {"next_dept": "permits_office", "reward": 0.02, "message": "Back to Permits Office."},
                },
            },
            "environment": {
                "clerk_intro": "Environmental clearance needs structural survey.",
                "actions": {
                    "request_clearance_with_survey": {
                        "requires": ["structural_survey"],
                        "next_dept": "environment",
                        "reward": 0.18,
                        "message": "Environmental clearance issued.",
                        "gives": ["env_clearance"],
                        "completes": "get_env_clearance",
                    },
                    "ask_about_deadlock": {
                        "next_dept": "environment",
                        "reward": 0.12,
                        "message": "Fire Safety can issue a Preliminary Site Assessment.",
                        "hint": "Visit Fire Safety and request_site_assessment.",
                    },
                    "go_to_fire_safety": {"next_dept": "fire_safety", "reward": 0.05, "message": "You head to Fire Safety."},
                    "go_back": {"next_dept": "permits_office", "reward": 0.02, "message": "Back to Permits Office."},
                },
            },
            "fire_safety": {
                "clerk_intro": "We can issue a Preliminary Site Assessment.",
                "actions": {
                    "request_site_assessment": {
                        "next_dept": "fire_safety",
                        "reward": 0.20,
                        "message": "Preliminary Site Assessment issued.",
                        "gives": ["site_assessment"],
                        "completes": "get_site_assessment",
                    },
                    "go_back": {"next_dept": "permits_office", "reward": 0.02, "message": "Back to Permits Office."},
                },
            },
            "architect": {
                "clerk_intro": "Architect stamp needs structural survey and fee receipt.",
                "actions": {
                    "get_stamp_with_survey_and_receipt": {
                        "requires": ["structural_survey", "architect_fee_receipt"],
                        "next_dept": "architect",
                        "reward": 0.18,
                        "message": "Architect stamp issued.",
                        "gives": ["architect_stamp"],
                        "completes": "get_architect_stamp",
                    },
                    "go_to_cashier": {"next_dept": "cashier", "reward": 0.04, "message": "You head to Cashier."},
                    "go_back": {"next_dept": "permits_office", "reward": 0.02, "message": "Back to Permits Office."},
                },
            },
            "cashier": {
                "clerk_intro": "Architect fee is $50.",
                "actions": {
                    "pay_architect_fee": {
                        "next_dept": "cashier",
                        "reward": 0.15,
                        "message": "Architect fee receipt issued.",
                        "gives": ["architect_fee_receipt"],
                        "completes": "pay_architect_fee",
                    },
                    "go_back": {"next_dept": "architect", "reward": 0.02, "message": "Back to Architect."},
                },
            },
            "neighbors": {
                "clerk_intro": "Neighbor consent can be filed only after architect stamp.",
                "actions": {
                    "collect_consent_with_stamp": {
                        "requires": ["architect_stamp"],
                        "next_dept": "neighbors",
                        "reward": 0.18,
                        "message": "Neighbor consent form filed.",
                        "gives": ["neighbor_consent"],
                        "completes": "get_neighbor_consent",
                    },
                    "go_back": {"next_dept": "permits_office", "reward": 0.02, "message": "Back to Permits Office."},
                },
            },
        },
        "milestones": [
            "get_site_assessment",
            "get_survey",
            "get_env_clearance",
            "pay_architect_fee",
            "get_architect_stamp",
            "get_neighbor_consent",
            "final_submission",
        ],
        "substitutions": {
            "env_clearance": "site_assessment",
        },
        "win_condition": {"inventory_has": ["construction_permit"]},
        "win_reward": 0.30,
    },
}


def get_task(task_id: str) -> Dict[str, Any]:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id '{task_id}'. Expected one of: {list(TASKS)}")
    return deepcopy(TASKS[task_id])


def list_tasks() -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for task_id, task in TASKS.items():
        result.append(
            {
                "id": task_id,
                "name": task["name"],
                "difficulty": task["difficulty"],
                "max_steps": task["max_steps"],
                "description": task["description"],
            }
        )
    return result


def check_win_condition(task: Dict[str, Any], inventory: List[str]) -> bool:
    required = task.get("win_condition", {}).get("inventory_has", [])
    return all(item in inventory for item in required)


def grade_progress(task: Dict[str, Any], completed_steps: List[str], won: bool) -> float:
    milestones = task.get("milestones", [])
    if not milestones:
        return 1.0 if won else 0.0
    completed = len([m for m in milestones if m in completed_steps])
    milestone_score = completed / len(milestones)
    return min(1.0, milestone_score + (0.2 if won else 0.0))


def grade_episode(task_id: str, completed_steps: List[str], inventory: List[str], step_number: int) -> float:
    """Deterministic episode grader score in [0, 1]."""
    task = get_task(task_id)
    won = check_win_condition(task, inventory)
    progress = grade_progress(task, completed_steps, won)
    max_steps = max(1, task.get("max_steps", 1))
    efficiency = max(0.0, 1.0 - (step_number / max_steps))
    score = (0.75 * progress) + (0.25 * efficiency)
    return max(0.0, min(1.0, score))
