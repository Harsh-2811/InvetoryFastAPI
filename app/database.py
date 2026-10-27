import os
from contextlib import asynccontextmanager
from pymongo import ASCENDING
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

uri = os.getenv("MONGODB_URL")
if not uri:
    raise RuntimeError("MONGODB_URL is required")

client = AsyncIOMotorClient(uri)
db = client[os.getenv("MONGODB_DB", "inventory")]


@asynccontextmanager
async def lifespan(app):
    await client.admin.command("ping")

    await db.products.create_index(
        [("sku", ASCENDING)], unique=True
    )
    await db.orders.create_index([("product_id", ASCENDING)])
    await db.orders.create_index([("status", ASCENDING)])
    await db.orders.create_index([("customer_email", ASCENDING)])
    await db.products.create_index([("is_active", ASCENDING)])

    yield
    client.close()
