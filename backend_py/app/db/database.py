from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.utils.logger import log

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

async def connect_to_mongo():
    try:
        log.info("Connecting to MongoDB...")
        db_instance.client = AsyncIOMotorClient(settings.mongodb_uri)
        # Check connection
        await db_instance.client.admin.command("ping")
        # In the Node.js Mongoose connection, the DB name used is implied by the connection string.
        # "mongodb+srv://.../ChatDB" -> Motor will target ChatDB.
        db_instance.db = db_instance.client.get_default_database()
        log.info(f"Successfully connected to MongoDB database '{db_instance.db.name}'")
    except Exception as e:
        log.error(f"Error connecting to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    log.info("Closing MongoDB connection...")
    if db_instance.client:
        db_instance.client.close()
        log.info("MongoDB connection closed.")

def get_db():
    return db_instance.db
