from typing import List, Dict


_STOP_WORDS = {
    "the", "and", "for", "with", "from", "this", "that",
    "have", "error", "warning", "info", "request", "response",
    "failed", "failure", "service", "user", "auth", "token",
}


def _extract_tokens(message: str) -> List[str]:
    tokens = []
    current = []

    for ch in message:
        if ch.isalnum() or ch in {".", "_"}:
            current.append(ch)
        else:
            if current:
                token = "".join(current).lower()
                if len(token) >= 4 and token not in _STOP_WORDS:
                    tokens.append(token)
                current = []
    if current:
        token = "".join(current).lower()
        if len(token) >= 4 and token not in _STOP_WORDS:
            tokens.append(token)

    return tokens


def verify_answer(answer: str, logs: List[Dict]) -> bool:
    """
    Simple grounding verification.

    Succeeds only if the answer references at least one
    non-trivial token extracted from ERROR log messages.
    """
    if not answer or not logs:
        return False

    ans = answer.lower()

    for log in logs:
        if log.get("level") != "ERROR":
            continue

        message = str(log.get("message", ""))
        tokens = _extract_tokens(message)

        for token in tokens:
            if token in ans:
                return True

    return False
