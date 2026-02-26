from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.responses import RedirectResponse
import httpx
from datetime import datetime
from bson import ObjectId
from app.db.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserCreate, UserLogin, UserResponse, AuthProvider
from app.core.security import hash_password, verify_password, create_access_token
from app.utils.cloudinary import upload_image
from app.core.config import settings
from app.utils.logger import log
import urllib.parse
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    if len(user_data.username) < 3 or len(user_data.username) > 20:
        raise HTTPException(status_code=400, detail="Username must be between 3 and 20 characters.")
    if not user_data.password or len(user_data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
        
    existing_email = await db["users"].find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists.")
        
    existing_username = await db["users"].find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already exists. Please choose another.")
        
    hashed_pwd = hash_password(user_data.password)
    
    new_user = {
        "username": user_data.username,
        "email": user_data.email,
        "password": hashed_pwd,
        "authProvider": AuthProvider.email.value,
        "profilePic": "",
        "friends": [],
        "friendRequests": [],
        "sentRequests": [],
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    result = await db["users"].insert_one(new_user)
    new_user_id = result.inserted_id
    
    token = create_access_token(str(new_user_id))
    
    # 7 days max age
    response.set_cookie(
        key="jwt",
        value=token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.node_env == "production"
    )
    
    return {
        "_id": str(new_user_id),
        "username": user_data.username,
        "email": user_data.email,
        "profilePic": "",
        "authProvider": AuthProvider.email.value
    }

@router.post("/login")
async def login(user_data: UserLogin, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db["users"].find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials.")
        
    if user.get("authProvider") == AuthProvider.google.value and not user.get("password"):
        raise HTTPException(status_code=400, detail="Please sign in with Google.")
        
    if not verify_password(user_data.password, user.get("password")):
        raise HTTPException(status_code=400, detail="Invalid credentials.")
        
    token = create_access_token(str(user["_id"]))
    response.set_cookie(
        key="jwt",
        value=token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=settings.node_env == "production"
    )
    
    return {
        "_id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "profilePic": user.get("profilePic", ""),
        "authProvider": user.get("authProvider")
    }

@router.post("/logout")
async def logout(response: Response):
    response.set_cookie("jwt", "", max_age=0)
    return {"message": "Logged out successfully."}

@router.get("/check")
async def check_auth(current_user: dict = Depends(get_current_user)):
    return {
        "_id": str(current_user["_id"]),
        "username": current_user["username"],
        "email": current_user["email"],
        "profilePic": current_user.get("profilePic", ""),
        "authProvider": current_user.get("authProvider"),
        "createdAt": current_user.get("createdAt")
    }

@router.put("/update-profile")
async def update_profile(request: Request, response: Response, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    body = await request.json()
    profile_pic = body.get("profilePic")
    username = body.get("username")
    
    fields_to_update = {}
    
    if username and username != current_user["username"]:
        username = username.strip()
        if len(username) < 3 or len(username) > 20:
            raise HTTPException(status_code=400, detail="Username must be between 3 and 20 characters.")
        existing = await db["users"].find_one({"username": username, "_id": {"$ne": current_user["_id"]}})
        if existing:
            raise HTTPException(status_code=400, detail="This username is already taken by someone else.")
        fields_to_update["username"] = username
        
    if profile_pic:
        secure_url = await upload_image(profile_pic)
        fields_to_update["profilePic"] = secure_url
        
    if not fields_to_update:
        raise HTTPException(status_code=400, detail="No changes provided to update.")
        
    fields_to_update["updatedAt"] = datetime.utcnow()
    
    await db["users"].update_one({"_id": current_user["_id"]}, {"$set": fields_to_update})
    
    updated_user = await db["users"].find_one({"_id": current_user["_id"]})
    
    token = create_access_token(str(updated_user["_id"]))
    response.set_cookie("jwt", value=token, max_age=7 * 24 * 60 * 60, httponly=True, samesite="lax", secure=settings.node_env == "production")
    
    updated_user["_id"] = str(updated_user["_id"])
    return updated_user

@router.get("/check-username/{username}")
async def check_username_availability(username: str, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    if not username or len(username.strip()) < 3:
        return {"available": False, "message": "Username must be at least 3 characters."}
    if len(username.strip()) > 20:
        return {"available": False, "message": "Username cannot be more than 20 characters."}
        
    if current_user["username"] == username:
        return {"available": True, "message": "This is your current username."}
        
    existing = await db["users"].find_one({"username": username})
    if existing:
        return {"available": False, "message": "Username is already taken."}
        
    return {"available": True, "message": "Username is available."}

@router.get("/google")
async def google_login():
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_callback_url,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)

@router.get("/google/callback")
async def google_callback(code: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    async with httpx.AsyncClient() as client:
        token_res = await client.post(token_url, data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "redirect_uri": settings.google_callback_url,
            "grant_type": "authorization_code"
        })
        if token_res.status_code != 200:
            log.error(f"Google auth error: {token_res.text}")
            return RedirectResponse(f"{settings.frontend_url}/login?error=google_auth_processing_error")
            
        access_token = token_res.json().get("access_token")
        
        # Get user info
        user_info_res = await client.get("https://www.googleapis.com/oauth2/v2/userinfo", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user_info = user_info_res.json()
        
    email = user_info.get("email")
    google_id = user_info.get("id")
    profile_pic = user_info.get("picture", "")
    base_username = email.split("@")[0]
    
    user = await db["users"].find_one({"email": email})
    
    if not user:
        # Check if username exists, append random if so
        username_check = await db["users"].find_one({"username": base_username})
        if username_check:
            base_username = f"{base_username}_{google_id[:5]}"
            
        new_user = {
            "username": base_username,
            "email": email,
            "googleId": google_id,
            "authProvider": AuthProvider.google.value,
            "profilePic": profile_pic,
            "friends": [],
            "friendRequests": [],
            "sentRequests": [],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
        res = await db["users"].insert_one(new_user)
        user_id = str(res.inserted_id)
    else:
        user_id = str(user["_id"])
        
    token = create_access_token(user_id)
    response = RedirectResponse(settings.frontend_url)
    response.set_cookie("jwt", value=token, max_age=7 * 24 * 60 * 60, httponly=True, samesite="lax", secure=settings.node_env == "production")
    return response
