from fastapi import Depends, HTTPException, Request, status
from app.core.security import verify_access_token
from app.db.database import get_db
from app.schemas.user import UserInDB
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

async def get_current_user(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)) -> dict:
    # 1. Extract token from cookie
    token = request.cookies.get("jwt")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized - No token provided"
        )
    
    # 2. Verify token
    user_id_str = verify_access_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized - Invalid or expired token"
        )
    
    # 3. Find user
    user = await db["users"].find_one({"_id": ObjectId(user_id_str)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
