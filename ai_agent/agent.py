from typing import Dict

from .retriever import retrieve_logs
from .grader import grade_logs
from .llm import generate_diagnosis_with_llm
from .verifier import verify_answer


MAX_RETRIES = 3
 

def run_agent(project_id: str, project_secret: str, service: str) -> Dict:
    
    """
    Main entry point for RADAR-AI diagnosis.

    Flow:
    - Retrieve logs for the project + service.
    - Grade logs for sufficiency and quality.
    - Call LLM to generate a diagnosis, with limited retries.
    - Verify that the diagnosis is grounded in the logs.
    - Fail safely if verification never passes.
    """
    logs = retrieve_logs(project_id, project_secret, service)
    print("RADAR DEBUG count:", len(logs))
    print("RADAR DEBUG messages:", [l.get("message") for l in logs])
    if not grade_logs(logs):
        return {
            "status": "failed",
            "project_id": project_id,
            "service": service,
            "reason": "Not enough useful logs to safely diagnose",
            "confidence": 0.0,
        }

    for attempt in range(MAX_RETRIES):
        diagnosis = generate_diagnosis_with_llm(service, logs)

        if verify_answer(diagnosis, logs):
            confidence = 0.7 + 0.1 * (MAX_RETRIES - 1 - attempt)
            confidence = round(min(max(confidence, 0.0), 1.0), 2)

            return {
                "status": "success",
                "project_id": project_id,
                "service": service,
                "diagnosis": diagnosis,
                "attempt": attempt + 1,
                "confidence": confidence,
            }

    return {
        "status": "failed",
        "project_id": project_id,
        "service": service,
        "reason": "Could not verify any diagnosis against logs",
        "confidence": 0.2,
    }
