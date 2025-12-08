from pydantic import BaseModel
from typing import Dict


class WebhookRequest(BaseModel):
    event: str
    data: Dict
