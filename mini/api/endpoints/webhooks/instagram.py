# File: mini/api/endpoints/webhooks/instagram.py

from fastapi import APIRouter, Request, Response, HTTPException
from config.config import config

router = APIRouter()

VERIFY_TOKEN = config.INSTAGRAM_CONFIG.verify_token

@router.get("/instagram")
async def verify_instagram_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return Response(content=challenge)
        else:
            raise HTTPException(status_code=403, detail="Invalid verify token")

    raise HTTPException(status_code=400, detail="Missing parameters")

@router.post("/instagram")
async def handle_instagram_webhook(request: Request):
    # For now, just acknowledge receipt of the webhook
    return {"status": "ok"}