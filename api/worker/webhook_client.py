"""
Webhook client for sending task events to external webhook endpoints.
Implements HMAC-SHA256 signature verification as per webhook specification.

Environment Variables:
    WEBHOOK_URL: The webhook endpoint URL (e.g., https://example.com/functions/v1/agent-webhook)
    WEBHOOK_SECRET: The webhook secret for HMAC signature generation

If these environment variables are not set, webhook sending will be skipped silently.
"""
import os
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import httpx, but handle gracefully if not available
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available - webhook functionality will be disabled")


def _generate_signature(timestamp: str, body: str, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for webhook authentication.
    
    Args:
        timestamp: Unix timestamp as string
        body: JSON stringified payload
        secret: Webhook secret key
        
    Returns:
        Hexadecimal signature string
    """
    signature_payload = f"{timestamp}.{body}"
    signature = hmac.new(
        secret.encode('utf-8'),
        signature_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return signature


def send_webhook(
    event_type: str,
    project_id: str,
    payload: Dict[str, Any],
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None
) -> bool:
    """
    Send a webhook event to the configured webhook endpoint.
    
    Args:
        event_type: Type of event (e.g., 'task.created', 'task.updated')
        project_id: Project ID associated with the event
        payload: Event-specific payload data
        webhook_url: Webhook URL (defaults to WEBHOOK_URL env var)
        webhook_secret: Webhook secret (defaults to WEBHOOK_SECRET env var)
        
    Returns:
        True if webhook was sent successfully, False otherwise
    """
    # Get webhook configuration from environment or parameters
    url = webhook_url or os.getenv("WEBHOOK_URL")
    secret = webhook_secret or os.getenv("WEBHOOK_SECRET")
    
    # If webhook is not configured, skip silently (not an error)
    if not url or not secret:
        missing = []
        if not url:
            missing.append("WEBHOOK_URL")
        if not secret:
            missing.append("WEBHOOK_SECRET")
        logger.info(f"Webhook not configured (missing: {', '.join(missing)}), skipping webhook for {event_type}")
        return False
    
    # Check if httpx is available
    if not HTTPX_AVAILABLE:
        logger.warning("httpx not available - cannot send webhook")
        return False
    
    try:
        import json
        
        # Generate timestamp in ISO 8601 format with milliseconds (e.g., 2024-12-04T15:30:00.000Z)
        # Match the exact format used by the webhook endpoint
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        # Prepare the webhook payload with timestamp included
        webhook_payload = {
            "event_type": event_type,
            "project_id": project_id,
            "timestamp": timestamp,
            "payload": payload
        }
        
        # Convert to JSON string (must be the exact string that will be sent)
        body_json = json.dumps(webhook_payload, sort_keys=True)
        
        # Create message to sign: timestamp.body (with dot separator as per spec)
        message = f"{timestamp}.{body_json}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "x-webhook-signature": signature,
            "x-webhook-timestamp": timestamp
        }
        
        # Send webhook request
        logger.info(f"Webhook: Sending {event_type} for project {project_id} to {url}")
        logger.debug(f"Webhook: Timestamp: {timestamp}, Message length: {len(message)}")
        with httpx.Client(timeout=10.0) as client:
            # Send the request with the exact JSON string we signed
            response = client.post(
                url,
                content=body_json,  # Use content= to send exact string, not json= which re-serializes
                headers=headers
            )
            
            # Check response
            if response.status_code == 200:
                logger.info(f"✅ Webhook sent successfully: {event_type} for project {project_id}")
                return True
            else:
                logger.warning(
                    f"⚠️ Webhook returned status {response.status_code}: {event_type} for project {project_id}. "
                    f"Response: {response.text[:200]}"
                )
                return False
            
    except httpx.RequestError as e:
        logger.error(f"❌ Failed to send webhook {event_type} for project {project_id}: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error sending webhook {event_type} for project {project_id}: {e}", exc_info=True)
        return False


def send_task_created_webhook(
    task_id: str,
    project_id: str,
    queue_name: str,
    task_type: str,
    status: str,
    agent_name: Optional[str] = None,
    context: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> bool:
    """
    Send a 'task.created' webhook event.
    
    Args:
        task_id: Celery task ID
        project_id: Project ID
        queue_name: Queue name
        task_type: Type of task ('agent_initialization' or 'agent_result_processing')
        status: Task status
        agent_name: Agent name (optional)
        context: Task context (optional)
        parent_task_id: Parent task ID (optional)
        result: Task result (optional)
        error: Error message (optional)
        
    Returns:
        True if webhook was sent successfully, False otherwise
    """
    payload = {
        "task_id": task_id,
        "queue_name": queue_name,
        "task_type": task_type,
        "status": status,
    }
    
    # Add optional fields
    if agent_name:
        payload["agent_name"] = agent_name
    if context:
        payload["context"] = context
    if parent_task_id:
        payload["parent_task_id"] = parent_task_id
    if result:
        payload["result"] = result
    if error:
        payload["error"] = error
    
    return send_webhook("task.created", project_id, payload)
