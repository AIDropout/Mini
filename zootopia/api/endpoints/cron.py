from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Security
from zootopia.core.security import verify_api_key
from zootopia.controller.tasks.revive import handle_revive

router = APIRouter()


@router.post("/cron")
async def cron_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key),
):
    """Endpoint hit by Supabase cron job every x minutes."""
    try:
        await handle_revive(background_tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
