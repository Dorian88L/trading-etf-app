from pydantic import BaseModel
from datetime import datetime
import uuid


class WatchlistBase(BaseModel):
    etf_isin: str


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistResponse(WatchlistBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True