from app.failure_engine import FailureContext

MAX_RETRIES = 3

ALLOWED_BY_CATEGORY = {
    "soft_decline": {"RETRY_SAME", "ESCALATE"},
    "needs_alt_method": {
        "SEND_PAYMENT_LINK",
        "RETRY_ALT_METHOD",
        "ESCALATE",
    },
    "hard_decline": {"ESCALATE"},
    "unknown": {"ESCALATE"},
}


def decide_action(
    ctx: FailureContext,
    category: str,
    proposal: dict,
) -> dict:

    proposed_action = proposal.get("action", "ESCALATE")

    # Unknown or invalid category → always escalate
    if category not in ALLOWED_BY_CATEGORY:
        return {
            "action": "ESCALATE",
            "override_reason": "Unknown failure category.",
        }

    # Retry limit reached → force escalation
    if ctx.retry_count >= MAX_RETRIES:
        return {
            "action": "ESCALATE",
            "override_reason": "Maximum retry limit reached.",
        }

    # Check whether Gemini's proposal is allowed
    allowed_actions = ALLOWED_BY_CATEGORY[category]

    if proposed_action not in allowed_actions:
        return {
            "action": "ESCALATE",
            "override_reason": (
                f"Action {proposed_action} is not allowed "
                f"for category {category}."
            ),
        }

    # Proposal passed all policy checks
    return {
        "action": proposed_action,
        "override_reason": None,
    }