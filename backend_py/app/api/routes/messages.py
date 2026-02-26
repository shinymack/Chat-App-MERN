from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.db.database import get_db
from app.api.deps import get_current_user
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.message import MessageCreate
from app.utils.cloudinary import upload_image
from app.sockets.socket_app import get_receiver_socket_id, sio
from datetime import datetime

router = APIRouter()

@router.get("/users")
async def get_users_for_sidebar(current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        users_cursor = db["users"].find(
            {"_id": {"$ne": current_user["_id"]}},
            {"password": 0} # hide password
        )
        users = await users_cursor.to_list(length=1000)
        
        for u in users:
            u["_id"] = str(u["_id"])
            if "friends" in u: u["friends"] = [str(fid) for fid in u["friends"]]
            if "friendRequests" in u: u["friendRequests"] = [str(fid) for fid in u["friendRequests"]]
            if "sentRequests" in u: u["sentRequests"] = [str(fid) for fid in u["sentRequests"]]
            if "createdAt" in u: u["createdAt"] = u["createdAt"].isoformat()
            if "updatedAt" in u: u["updatedAt"] = u["updatedAt"].isoformat()
            
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{user_to_chat_id}")
async def get_messages(user_to_chat_id: str, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        other_id = ObjectId(user_to_chat_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
    my_id = current_user["_id"]
    
    messages_cursor = db["messages"].find({
        "$or": [
            {"senderId": my_id, "receiverId": other_id},
            {"senderId": other_id, "receiverId": my_id}
        ]
    }).sort("createdAt", 1)
    
    messages = await messages_cursor.to_list(length=1000)
    for m in messages:
        m["_id"] = str(m["_id"])
        m["senderId"] = str(m["senderId"])
        m["receiverId"] = str(m["receiverId"])
        if "createdAt" in m: m["createdAt"] = m["createdAt"].isoformat()
        if "updatedAt" in m: m["updatedAt"] = m["updatedAt"].isoformat()
        
    return messages

@router.post("/send/{receiver_id}")
async def send_message(receiver_id: str, message_data: MessageCreate, current_user: dict = Depends(get_current_user), db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        recv_obj_id = ObjectId(receiver_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")
        
    image_url = None
    if message_data.image:
        image_url = await upload_image(message_data.image)
        
    new_message = {
        "senderId": current_user["_id"],
        "receiverId": recv_obj_id,
        "text": message_data.text,
        "image": image_url,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
    
    result = await db["messages"].insert_one(new_message)
    new_message["_id"] = str(result.inserted_id)
    new_message["senderId"] = str(new_message["senderId"])
    new_message["receiverId"] = str(new_message["receiverId"])
    new_message["createdAt"] = new_message["createdAt"].isoformat()
    new_message["updatedAt"] = new_message["updatedAt"].isoformat()
    
    receiver_socket_id = get_receiver_socket_id(receiver_id)
    if receiver_socket_id:
        await sio.emit("newMessage", new_message, to=receiver_socket_id)
        
    return new_message
