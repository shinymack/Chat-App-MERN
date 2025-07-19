import { X } from "lucide-react";
import { useAuthStore } from "../store/useAuthStore";
import { useChatStore } from "../store/useChatStore";

const ChatHeader = () => {
    const { onlineUsers } = useAuthStore();
    const { selectedUser, setSelectedUser } = useChatStore();
    return (
        <div className="p-2.5 border-b border-base-300">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {/* ProfilePic  */}
                    <div className="avatar">
                        <div className="size-10 rounded-full relative">
                            <img
                                src={selectedUser.profilePic || "/avatar.png"}
                                alt={selectedUser.userName}
                            />
                        </div>
                    </div>
                    {/* UserInfo  */}
                    <div>
                        <h3 className="font-medium">{selectedUser.username}</h3>
                        <p className="text-sm text-base-content/70">
                            {onlineUsers.includes(selectedUser._id) ? "Online": "Offline"}
                        </p>
                    </div>
                </div>
                <button onClick={() => {
                    setSelectedUser(null);
                }}> <X /> </button>
            </div>
        </div>
    );
};

export default ChatHeader;
