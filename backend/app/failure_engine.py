from dataclasses import dataclass, asdict


@dataclass
class FailureContext:
    payment_id: str
    order_id: str
    amount: int  # in paise
    error_code: str
    error_reason: str
    error_description: str
    retry_count: int = 0


RETRIABLE_REASONS = {
    "payment_timed_out": "soft_decline",
    "gateway_technical_error": "soft_decline",
    "insufficient_fund": "needs_alt_method",
}


NON_RETRIABLE_REASONS = {
    "card_declined": "hard_decline",
    "invalid_card": "hard_decline",
    "expired_card": "hard_decline",
}


def classify(reason: str) -> str:
    if reason in RETRIABLE_REASONS:
        return RETRIABLE_REASONS[reason]

    if reason in NON_RETRIABLE_REASONS:
        return NON_RETRIABLE_REASONS[reason]

    return "unknown"


async def process_failure(ctx: FailureContext) -> dict:
    category = classify(ctx.error_reason)

    from app.ai_agent import propose_action
    from app.policy_engine import decide_action
    from app.executor import execute_action
    from app.audit import log_event

    await log_event(
        "failure_detected",
        asdict(ctx) | {"category": category}
    )

    # Gemini proposes an action
    proposal = await propose_action(ctx, category)

    # Policy Engine validates the proposal
    decision = decide_action(
        ctx,
        category,
        proposal
    )

    # Executor performs ONLY the approved action
    outcome = await execute_action(
        ctx,
        decision
    )

    result = {
        "payment_id": ctx.payment_id,
        "category": category,
        "llm_proposed_action": proposal["action"],
        "llm_reasoning": proposal["reasoning"],
        "final_action_taken": decision["action"],
        "policy_overridden": (
            decision["action"] != proposal["action"]
        ),
        "override_reason": decision.get("override_reason"),
        "outcome": outcome,
    }

    # Record the complete recovery decision
    await log_event(
        "recovery_completed",
        result
    )

    return result