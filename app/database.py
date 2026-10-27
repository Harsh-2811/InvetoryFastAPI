import os
from contextlib import asynccontextmanager
from pymongo import ASCENDING
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

client = None
db = None


@asynccontextmanager
async def lifespan(app):
    global client, db
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("MONGODB URI is not required")
    
    client = AsyncIOMotorClient(uri)
    await client.admin.command("ping")

    db = client(os.getenv("MONGODB_DB", "inventory"))
    await db.products.create_index(
        [("sku", ASCENDING)], unique=True
    )
    await db.orders.create_index([("product_id", ASCENDING)])
    await db.orders.create_index([("status", ASCENDING)])
    await db.orders.create_index([("customer_email", ASCENDING)])
    await db.products.create_index([("is_active", ASCENDING)])

    await db.orders.create()

    yield
    client.close()
    
