import socketio
from typing import Dict, Optional

# Equivalent of maintaining userSocketMap in Node
user_socket_map: Dict[str, str] = {} # {userId: socketId}

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:5173", "https://chatty-osx6.onrender.com", "https://shinychat.onrender.com"]
)

def get_receiver_socket_id(receiver_id: str) -> Optional[str]:
    return user_socket_map.get(str(receiver_id))

@sio.event
async def connect(sid, environ):
    # Retrieve query parameters mimicking standard URL search params
    # In ASGI environ, queries are in QUERY_STRING
    query_string = environ.get("QUERY_STRING", "")
    queries = dict(q.split("=") for q in query_string.split("&") if "=" in q)
    user_id = queries.get("userId")
    
    if user_id:
        user_socket_map[user_id] = sid
        # Broadcast online users equivalent to io.emit("getOnlineUsers", ...)
        await sio.emit("getOnlineUsers", list(user_socket_map.keys()))

@sio.event
async def disconnect(sid):
    disconnected_user = None
    for user_id, mapped_sid in list(user_socket_map.items()):
        if mapped_sid == sid:
            disconnected_user = user_id
            del user_socket_map[user_id]
            break

    if disconnected_user:
        await sio.emit("getOnlineUsers", list(user_socket_map.keys()))
