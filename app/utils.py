from bson import ObjectId
from fastapi import HTTPException

def to_object_id(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(400, details = "Invalid object id")

    return ObjectId(value)

def serialize(doc):
    if doc is None:
        return None
    
    doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("product_id"), ObjectId):
        doc["product_id"] = str(doc["product_id"])
    
    return doc