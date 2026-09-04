import os
import razorpay
from dotenv import load_dotenv

load_dotenv()

client = razorpay.Client(
    auth=(
        os.getenv("RAZORPAY_KEY_ID"),
        os.getenv("RAZORPAY_KEY_SECRET"),
    )
)


async def execute_action(ctx, decision: dict) -> dict:
    action = decision["action"]

    if action == "RETRY_SAME":
        order = client.order.create({
            "amount": ctx.amount,
            "currency": "INR",
            "notes": {
                "retry_of": ctx.payment_id
            }
        })

        return {
            "status": "retry_order_created",
            "new_order_id": order["id"]
        }

    if action == "RETRY_ALT_METHOD":
        order = client.order.create({
            "amount": ctx.amount,
            "currency": "INR",
            "notes": {
                "retry_of": ctx.payment_id,
                "method": "alt"
            }
        })

        return {
            "status": "retry_alt_order_created",
            "new_order_id": order["id"]
        }

    if action == "SEND_PAYMENT_LINK":
        link = client.payment_link.create({
            "amount": ctx.amount,
            "currency": "INR",
            "description": f"Retry payment for order {ctx.order_id}",
            "notes": {
                "original_payment_id": ctx.payment_id
            }
        })

        return {
            "status": "payment_link_sent",
            "link": link["short_url"]
        }

    if action == "ESCALATE":
        return {
            "status": "escalated_for_human_review"
        }

    return {
        "status": "no_action_taken"
    }