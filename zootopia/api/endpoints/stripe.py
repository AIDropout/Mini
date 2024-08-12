from fastapi import APIRouter, Request, HTTPException
from zootopia.core.logger import logger
from zootopia.controller.tasks.respond import handle_respond
import stripe
import os

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY_TEST")

@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Webhook for Stripe events"""
    
    try:
        # Get the raw body and signature
        body = await request.body()
        signature = request.headers.get("stripe-signature")

        # Verify the event
        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=signature,
                secret=os.getenv("STRIPE_WEBHOOK_SECRET")
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")

        # Process the event
        if event["type"] == "checkout.session.completed":
            logger.info("🔔 Payment succeeded!")
        elif event["type"] == "customer.subscription.trial_will_end":
            logger.info("Subscription trial will end")
        elif event["type"] == "customer.subscription.created":
            logger.info(f"Subscription created {event.id}")
        elif event["type"] == "customer.subscription.updated":
            logger.info(f"Subscription updated {event.id}")
        elif event["type"] == "customer.subscription.deleted":
            logger.info(f"Subscription canceled: {event.id}")
        elif event["type"] == "entitlements.active_entitlement_summary.updated":
            logger.info(f"Active entitlement summary updated: {event.id}")
        else:
            logger.info(f"Unhandled event type {event['type']}")

        # Schedule processing
        handle_respond(event)
        return {"status": "Message received and processing scheduled"}
    except Exception as e:
        logger.exception("Error in stripe_webhook")
        raise HTTPException(status_code=500, detail=str(e))