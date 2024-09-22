from fastapi import Request, HTTPException, Depends
from .models import InstagramWebhook

async def validate_instagram_webhook(request: Request) -> InstagramWebhook:
    try:
        body = await request.json()
        return InstagramWebhook.model_validate(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid webhook payload: {str(e)}")
    
