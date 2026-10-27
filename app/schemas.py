
from pydantic import BaseModel, Field, EmailStr
from decimal import Decimal
from typing import Literal
"""
Validate name (2–150 characters), price greater than 0 with 2 decimal places,
stock_quantity 0 or more
SKU must be unique (uppercase letters, digits and dashes); a duplicate returns 409
Conflict
Return 404 if the product is not found; prevent changing product_id
"""

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    sku: str = Field(pattern = r"^[A-Z0-9-]+$")
    price: Decimal = Field(
        gt=0, max_digit = 12, decimal_places = 2
    )
    stock_quantity:int = Field(ge=0)
    is_active:bool = True

class ProductUpdate(BaseModel):
    name:str | None = Field(
        default = None, min_length = 2, max_length = 150
    )
    sku: str | None = Field(default = None, pattern = r"^[A-Z0-9-]+$")
    price: Decimal | None = Field(
        default = None, gt=0, max_digit = 12, decimal_places = 2
    )
    stock_quantity:int | None = Field(default = None,  ge=0)
    is_active:bool | None = None

class OrderCreate(BaseModel):
    product_id: str
    customer_email: EmailStr
    quantity: int = Field(ge=1)

class StatusUpdate(BaseModel):
    status: Literal["pending" , "confirmed" , "shipped" , "cancelled" ]