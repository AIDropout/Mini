from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Security
from zootopia.core.security import verify_api_key
from zootopia.controller.tasks.revive import handle_revive
from zootopia.utils.utils import is_ngrok_url
from zootopia.core.logger import logger

router = APIRouter()


@router.post("/cron")
async def cron_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key),
):
    """Endpoint hit by Supabase cron job every x minutes."""
    try:
        await handle_revive(background_tasks, dev_mode=is_ngrok_url(str(request.base_url)))
    except Exception as e:
        logger.exception(f"Error in cron webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
