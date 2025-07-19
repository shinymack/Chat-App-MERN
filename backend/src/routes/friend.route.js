import express from "express";
import {
    sendFriendRequest,
    acceptFriendRequest,
    rejectFriendRequest,
    removeFriend,
    getFriends,
    getPendingRequests,
    getSentRequests
} from "../controllers/friend.controller.js";
import { protectRoute } from "../middleware/auth.middleware.js"; // Assuming you have this

const router = express.Router();

// All routes here should be protected
router.use(protectRoute);

// Send a friend request to a user
router.post("/request/send/", sendFriendRequest);

// Accept a friend request from a user
router.post("/request/accept/:senderId", acceptFriendRequest);

// Reject a friend request from a user
router.post("/request/reject/:senderId", rejectFriendRequest);

// Remove a friend
router.delete("/remove/:friendId", removeFriend);

// Get the current user's friends list
router.get("/list", getFriends);

// Get pending friend requests for the current user
router.get("/requests/pending", getPendingRequests);

// Get sent friend requests by the current user
router.get("/requests/sent", getSentRequests);


export default router;