from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pymongo import DESCENDING, ReturnDocument

from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from app.database import db
from app.schemas import OrderCreate, StatusUpdate
from app.utils import serialize, to_object_id

router = APIRouter(prefix="/orders")

VALID_STATUSES = {
    "pending" , "confirmed" , "shipped" , "cancelled" 
}


@router.post("", status_code = 201)
async def create_order(payload: OrderCreate):
    product_oid = to_object_id(payload.product_id)
    product = await db.products.find_one_and_update(
        {
            "_id": product_oid,
            "is_active": True,
            "stock_quantity": {"$gte": payload.quantity}
        },
        {
            "$inc": {
                "stock_quantity": -payload.quantity
            }
        },
        return_document = ReturnDocument.BEFORE
    )

    if product is None:
        existing = await db.products.find_one(
            {"_id": product_oid}
        )
        if not existing:
            raise HTTPException(404, "product not found")
        
        if not existing["is_active"]:
            raise HTTPException(409, "product not active")

        raise HTTPException(409, "insufficient stock")
    
    total = (
        Decimal(str(product["price"])) * payload.quantity
    ).quantize(Decimal("0.01"), rounding = ROUND_HALF_UP)


    order = {
        "product_id": product_oid,
        "customer_email": str(payload.customer_email),
        "quantity": payload.quantity,
        "unit_price": float(product["price"]),
        "total_amount": float(total),
        "status": "pending",
        "created_at": datetime.now(timezone.utc)
    }

    try:
        result = await db.orders.insert_one(order)

    except Exception:
        await db.products.update_one(
            {"_id": product_oid},
            {"$inc": {"stock_quantity": payload.quantity}}
        )
        raise 

    created = await db.orders.find_one({
        "_id": result.inserted_id
    })
    return serialize(created)


@router.get("")
async def list_orders(
    status: Optional[str] = None, 
    product_id : Optional[str] = None,
    customer_email: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    filters= {}
    if status is not None:
        if status not in VALID_STATUSES:
            raise HTTPException(422, "Invalid status")
        filters["status"] = status

    if product_id is not None:
        filters["product_id"] = to_object_id(product_id)

    if customer_email is not None:
        filters["customer_email"] = customer_email
    
    total = await db.orders.count_documents(filters)

    cursor = (
        db.orders.find(filters).sort("_id", DESCENDING)
        .skip(offset)
        .limit(limit)
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items":[serialize(doc) async for doc in cursor]
    }

@router.get("/{order_id}")
async def get_order(order_id: str):
    order = await db.orders.find_one(
        {"_id": to_object_id(order_id)}
    )
    if not order:
        raise HTTPException(
            404,
            detail = "order not exists"
        )
    return serialize(order)


@router.patch("/{order_id}/status")
async def update_order(order_id: str, payload: StatusUpdate):
    order_oid = to_object_id(order_id)
    order = await db.orders.find_one({"_id": order_oid})

    if not order:
        raise HTTPException(404, "Order not found")
    
    old_status = order["status"]
    new_status = payload.status

    if old_status == new_status:
        return serialize(order)
    
    updated = await db.orders.find_one_and_update({
        "_id": order_oid, "status": old_status
    }, {"$set": {"status": new_status}},
    return_document = ReturnDocument.AFTER,
    )

    if not updated:
        raise HTTPException(409, "Order was modified concurrently, retry")

    if new_status == "cancelled":
        await db.products.update_one(
            {"_id": order["product_id"]},
            {"$inc": {"stock_quantity": order["quantity"]}}
        )

    return serialize(updated)


@router.delete("/{order_id}")
async def delete_order(order_id: str):
    order_oid = to_object_id(order_id)
    order = await db.orders.find_one_and_delete(
        {
            "_id": order_oid,
            "status": "pending"
        }
    )
    if order:
        await db.products.update_one(
            {
                "_id": order["product_id"]
            },
            {
                "$inc": {"stock_quantity": order["quantity"]}
            }
        )
        return {"message": "order deleted"}

    if not await db.orders.find_one({"_id": order_oid}):
        raise HTTPException(404, "Order not found")
    raise HTTPException(409, "Only pending orders can be deleted")
