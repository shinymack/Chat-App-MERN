from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from bson import ObjectId
from app.db.database import get_db
from app.api.deps import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.utils.logger import log

router = APIRouter()

class FriendRequestInput(BaseModel):
    identifier: str

@router.post("/request/send")
async def send_friend_request(req: FriendRequestInput, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    identifier = req.identifier
    if not identifier:
        raise HTTPException(status_code=400, detail="Username or email is required.")
        
    receiver = await db["users"].find_one({
        "$or": [{"username": identifier}, {"email": identifier}]
    })
    
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found.")
        
    sender_id = current_user["_id"]
    receiver_id = receiver["_id"]
    
    if str(sender_id) == str(receiver_id):
        raise HTTPException(status_code=400, detail="You cannot send a friend request to yourself.")
        
    if receiver_id in current_user.get("friends", []):
        raise HTTPException(status_code=400, detail="You are already friends with this user.")
        
    if receiver_id in current_user.get("sentRequests", []):
        raise HTTPException(status_code=400, detail="Friend request already sent.")
        
    if receiver_id in current_user.get("friendRequests", []):
        raise HTTPException(status_code=400, detail="This user has already sent you a friend request.")
        
    await db["users"].update_one(
        {"_id": sender_id},
        {"$push": {"sentRequests": receiver_id}}
    )
    
    await db["users"].update_one(
        {"_id": receiver_id},
        {"$push": {"friendRequests": sender_id}}
    )
    
    return {"message": "Friend request sent successfully."}

@router.post("/request/accept/{sender_id}")
async def accept_friend_request(sender_id: str, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        sender_obj_id = ObjectId(sender_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
    receiver_id = current_user["_id"]
    
    sender = await db["users"].find_one({"_id": sender_obj_id})
    if not sender:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if sender_obj_id not in current_user.get("friendRequests", []):
        raise HTTPException(status_code=400, detail="Friend request not found or already handled.")
        
    await db["users"].update_one(
        {"_id": receiver_id},
        {
            "$push": {"friends": sender_obj_id},
            "$pull": {"friendRequests": sender_obj_id}
        }
    )
    
    await db["users"].update_one(
        {"_id": sender_obj_id},
        {
            "$push": {"friends": receiver_id},
            "$pull": {"sentRequests": receiver_id}
        }
    )
    
    return {"message": "Friend request accepted."}

@router.post("/request/reject/{sender_id}")
async def reject_friend_request(sender_id: str, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        sender_obj_id = ObjectId(sender_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
    receiver_id = current_user["_id"]
    
    # Check
    if sender_obj_id not in current_user.get("friendRequests", []):
        raise HTTPException(status_code=400, detail="Friend request not found or already handled.")
        
    await db["users"].update_one(
        {"_id": receiver_id},
        {"$pull": {"friendRequests": sender_obj_id}}
    )
    
    await db["users"].update_one(
        {"_id": sender_obj_id},
        {"$pull": {"sentRequests": receiver_id}}
    )
    
    return {"message": "Friend request rejected."}

@router.delete("/remove/{friend_id}")
async def remove_friend(friend_id: str, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        friend_obj_id = ObjectId(friend_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
    if friend_obj_id not in current_user.get("friends", []):
        raise HTTPException(status_code=400, detail="This user is not in your friends list.")
        
    await db["users"].update_one(
        {"_id": current_user["_id"]},
        {"$pull": {"friends": friend_obj_id}}
    )
    
    await db["users"].update_one(
        {"_id": friend_obj_id},
        {"$pull": {"friends": current_user["_id"]}}
    )
    
    return {"message": "Friend removed successfully."}

async def fetch_populated_users(db: AsyncIOMotorDatabase, user_ids: list):
    if not user_ids:
        return []
    users = await db["users"].find(
        {"_id": {"$in": user_ids}},
        {"username": 1, "email": 1, "profilePic": 1, "_id": 1}
    ).to_list(length=1000)
    
    # Fix ObjectId stringification
    for u in users:
        u["_id"] = str(u["_id"])
    return users

@router.get("/list")
async def get_friends(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await fetch_populated_users(db, current_user.get("friends", []))

@router.get("/requests/pending")
async def get_pending_requests(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await fetch_populated_users(db, current_user.get("friendRequests", []))

@router.get("/requests/sent")
async def get_sent_requests(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    return await fetch_populated_users(db, current_user.get("sentRequests", []))
