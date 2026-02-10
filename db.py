# db.py

import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from info import MONGO_URI, DB_NAME

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.users = self.db["users"]
        self.settings = self.db["settings"]

    # ---------------------------
    # User premium
    # ---------------------------
    async def set_premium(self, user_id: int, expiry_time: datetime.datetime):
        await self.users.update_one(
            {"_id": user_id},
            {"$set": {"expiry_time": expiry_time}},
            upsert=True
        )

    async def remove_premium(self, user_id: int):
        await self.users.update_one(
            {"_id": user_id},
            {"$unset": {"expiry_time": ""}},
            upsert=True
        )

    async def get_user(self, user_id: int):
        return await self.users.find_one({"_id": user_id})

    async def get_all_users(self):
        async for u in self.users.find({}):
            yield u

    # ---------------------------
    # Bot settings (inside bot)
    # ---------------------------
    async def get_mode(self):
        s = await self.settings.find_one({"_id": "mode"})
        if not s:
            return {"auto_remove": True, "remind": False}
        return s["value"]

    async def set_mode(self, auto_remove: bool, remind: bool):
        await self.settings.update_one(
            {"_id": "mode"},
            {"$set": {"value": {"auto_remove": auto_remove, "remind": remind}}},
            upsert=True
        )

db = Database()
