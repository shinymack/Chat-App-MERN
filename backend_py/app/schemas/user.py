from pydantic import BaseModel, Field, GetCoreSchemaHandler, ConfigDict
from pydantic_core import core_schema
from typing import Any, List, Optional
from bson import ObjectId
from datetime import datetime
from enum import Enum

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate)
            ])
        ])

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class AuthProvider(str, Enum):
    email = "email"
    google = "google"

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str

class UserCreate(UserBase):
    password: Optional[str] = Field(None, min_length=6)

class UserLogin(BaseModel):
    email: str
    password: Optional[str] = None

class UserInDB(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    password: Optional[str] = None
    profilePic: str = ""
    friends: List[PyObjectId] = []
    friendRequests: List[PyObjectId] = []
    sentRequests: List[PyObjectId] = []
    authProvider: AuthProvider = AuthProvider.email
    googleId: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

class UserResponse(UserBase):
    id: PyObjectId = Field(alias="_id")
    profilePic: str
    authProvider: AuthProvider
    createdAt: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)

class FriendResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    username: str
    email: str
    profilePic: str

    model_config = ConfigDict(populate_by_name=True)
