from fastapi import APIRouter
from .models import WebhookRequest

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("")
def webhook(webhook_data: WebhookRequest):
    """Handle webhook events"""
    return {
        "event": webhook_data.event,
        "data": webhook_data.data,
        "status": "processed",
        "message": "Webhook received and processed"
    }
