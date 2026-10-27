from fastapi import APIRouter, Query, HTTPException
from pymongo import DESCENDING, ReturnDocument

from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from app.database import db
from app.schemas import ProductCreate, ProductUpdate
from app.utils import serialize, to_object_id

router = APIRouter(prefix="/products")

@router.post("", status_code = 201)
async def create_product(payload: ProductCreate):
    data = payload.model_dump()
    data["price"] = float(data["price"])
    data["created_at"] = datetime.now(timezone.utc)

    try:
        result = await db.products.insert_one(data)
    except DuplicateKeyError:
        raise HTTPException(409, details="Duplicate SKU")

    product = await db.products.find_one(
        {"_id": result.inserted_id}
    )
    return serialize(product)


@router.get("")
async def list_products(
    is_active: bool | None = None, 
    in_stock : bool | None = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    filters= {}
    if is_active is not None:
        filters["is_active"] = is_active
    if in_stock is True:
        filters["stock_quantity"] = {"$gt": 0}
    elif in_stock is False:
        filters["stock_quantity"] = 0 
    
    total = await db.products.count_documents(filters)

    cursor = (
        db.products.find(filters).sort("_id", DESCENDING)
        .skip(offset)
        .limit(limit)
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items":[serialize(doc) async for doc in cursor]
    }

@router.get("/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one(
        {"_id": to_object_id(product_id)}
    )
    if not product:
        raise HTTPException(
            404,
            details = "Product not exists"
        )
    return serialize(product)


@router.patch("/{product_id}")
async def update_product(product_id: str, payload: ProductUpdate):
    updates = payload.model_dump(exclude_unset = True)
    if not updates:
        raise HTTPException(400, "No. fields provided")
    
    if any(value is None for value in updates.values()):
        raise HTTPException(400, "product field can not be none")

    if "price" in updates:
        updates["price"] = float(updates["price"])

    
    try:
        product = await db.products.find_one_and_update({
            "_id": to_object_id(product_id)
        },
        {
            "$set": updates
        }, 
        return_document = ReturnDocument.after)
    
    except DuplicateKeyError:
        raise HTTPException(409, "Duplicate SKU")
    
    if not product:
        raise HTTPException(404, "Product Not Found")

    return serialize(product)

@router.put("/{product_id}")
async def update_product(product_id: str, payload: ProductCreate):
    updates = payload.model_dump(exclude_unset = True)
    if "price" in updates:
        updates["price"] = float(updates["price"])

    
    try:
        product = await db.products.find_one_and_update({
            "_id": to_object_id(product_id)
        },
        {
            "$set": updates
        }, 
        return_document = ReturnDocument.after)
    
    except DuplicateKeyError:
        raise HTTPException(409, "Duplicate SKU")
    
    if not product:
        raise HTTPException(404, "Product Not Found")

    return serialize(product)

@router.delete("/{product_id}")
async def delete_product(product_id: str):
    product_id = to_object_id(product_id)
    active_order = await db.orders.find_one(
        {
            "product_id": product_oid,
        "status": {"$in": ["pending", "confirmed"]}
        }
    )
    if active_order:
        raise  HTTPException(409, "Product with active order")
    result = await db.products.delete_one({
        "_id": product_oid
    })

    if result.deleted_count == 0:
        raise HTTPException(404, "Product Not Found")
    
    return {"message": "Product Deleted"}


@router.get("/{product_id}/orders")
async def list_product_orders(
    product_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    product_id = to_object_id(product_id)
    product = await db.products.find_one(
        {"_id": to_object_id(product_id)}
    )
    if not product:
        raise HTTPException(
            404,
            details = "Product not exists"
        )
    
    filters = {"product_id": product_oid}
    total = await db.orders.count_documents(filters)

    cursor = (
        db.orders.find(filters)
        .sort("_id", DESCENDING)
        .skip(offset)
        .limit(limt)
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items":[serialize(doc) async for doc in cursor]
    }