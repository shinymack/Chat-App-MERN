from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import PyObjectId

class MessageBase(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None

class MessageCreate(MessageBase):
    pass

class MessageInDB(MessageBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    senderId: PyObjectId
    receiverId: PyObjectId
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

class MessageResponse(MessageInDB):
    pass
