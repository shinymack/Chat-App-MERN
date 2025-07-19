import toast from "react-hot-toast";
import { create } from "zustand";
import { axiosInstance } from "../lib/axios";
import { useAuthStore } from "./useAuthStore";


export const useChatStore = create((set, get) => ({
    messages:[],
    users: [],
    pendingRequests: [],
    sentRequests: [],
    selectedUser: null,
    isUsersLoading: false,
    isMessagesLoading: false,

    isFriendBoxOpen: false,

    toggleFriendsBox: () => set(state => ({ isFriendsBoxOpen: !state.isFriendsBoxOpen })),


    getFriends: async () => {
        set({isUsersLoading: true});
        try {
            const res = await axiosInstance.get("/friends/list");
            set({ users: res.data});
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to fetch friends");
        } finally {
            set({ isUsersLoading: false});
        }
    },
    getPendingRequests: async () => {
        try {
            const res = await axiosInstance.get("/friends/requests/pending");
            set({ pendingRequests: res.data });
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to fetch pending requests");
        }
    },

    getSentRequests: async () => {
        try {
            const res = await axiosInstance.get("/friends/requests/sent");
            set({ sentRequests: res.data });
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to fetch sent requests");
        }
    },

    sendFriendRequest: async (identifier) => {
        try {
            const res = await axiosInstance.post("/friends/request/send", { identifier });
            toast.success(res.data.message);
            // Refresh sent requests list
            get().getSentRequests();
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to send request");
        }
    },
    acceptFriendRequest: async (senderId) => {
        try {
            const res = await axiosInstance.post(`/friends/request/accept/${senderId}`);
            toast.success(res.data.message);
            // Refresh both friends and pending requests lists
            get().getFriends();
            get().getPendingRequests();
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to accept request");
        }
    },

    rejectFriendRequest: async (senderId) => {
        try {
            const res = await axiosInstance.post(`/friends/request/reject/${senderId}`);
            toast.success(res.data.message);
            // Refresh pending requests list
            get().getPendingRequests();
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to reject request");
        }
    },
    removeFriend: async (friendId) => {
        try {
            const res = await axiosInstance.delete(`/friends/remove/${friendId}`);
            toast.success(res.data.message);
            // Refresh friends list
            get().getFriends();
            // Also deselect user if they were the one being chatted with
            if (get().selectedUser?._id === friendId) {
                set({ selectedUser: null });
            }
        } catch (error) {
            toast.error(error.response?.data?.message || "Failed to remove friend");
        }
    },

    getMessages: async (userId) => {
        set({isMessagesLoading: true});
        try {
            const res = await axiosInstance.get(`/messages/${userId}`);
            set({messages: res.data});
        } catch (error) {
            toast.error(error.response.data.message);
        } finally {
            set({isMessagesLoading: false});
        }
    },
    sendMessage: async (messageData) => {
        const {selectedUser, messages} = get();
        try {
            const res = await axiosInstance.post(`/messages/send/${selectedUser._id}`, messageData);
            set({messages : [...messages, res.data]});
        } catch (error){
            toast.error(error.response.data.message);
        }

    },


    subscribeToMessages: () => {
        const { selectedUser } = get();
        if(!selectedUser) return;
        
        const socket = useAuthStore.getState().socket;
        socket.on("newMessage", (newMessage) => {
            if(newMessage.senderId !== selectedUser._id) return
            set({
                messages: [...get().messages, newMessage]
            })
        })
    },

    unsubscribeFromMessages: () => {
        const socket = useAuthStore.getState().socket;
        socket.off("newMessage");
    },
    
    setSelectedUser: (selectedUser) => set({selectedUser})

}))

