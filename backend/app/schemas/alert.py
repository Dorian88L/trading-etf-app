from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from app.models.alert import AlertType


class AlertBase(BaseModel):
    alert_type: AlertType
    title: str
    message: str
    etf_isin: Optional[str] = None


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True