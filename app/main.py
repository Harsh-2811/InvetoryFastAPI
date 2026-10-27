from dotenv import load_dotenv
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.routes.products import products_router

app = FastAPI(title = "Inventory and Order API", version = "1.0.0")

app.include_router(products_router)
@app.get("/heath")
async def heath():
    return {"status": "ok"}