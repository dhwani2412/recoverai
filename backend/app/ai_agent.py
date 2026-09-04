import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ALLOWED_ACTIONS = [
    "RETRY_SAME",
    "RETRY_ALT_METHOD",
    "SEND_PAYMENT_LINK",
    "ESCALATE",
]

SYSTEM_INSTRUCTION = f"""
You are a payment recovery advisor.

You NEVER execute actions.
You ONLY propose one action from this list:

{ALLOWED_ACTIONS}

Always respond with strict JSON:
{{
    "action": "...",
    "reasoning": "..."
}}

The reasoning must be under 40 words.
"""


async def propose_action(ctx, category: str) -> dict:
    prompt = f"""
Payment failure details:

- amount: {ctx.amount / 100} INR
- error_reason: {ctx.error_reason}
- category: {category}
- retry_count so far: {ctx.retry_count}

Propose the single best next action and a short reasoning.
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
            ),
        )

        parsed = json.loads(response.text)

        if parsed.get("action") not in ALLOWED_ACTIONS:
            return {
                "action": "ESCALATE",
                "reasoning": "LLM proposed an invalid action; defaulting to escalation.",
            }

        return parsed

    except Exception as e:
        return {
            "action": "ESCALATE",
            "reasoning": f"AI unavailable ({type(e).__name__}); escalating for safety.",
        }