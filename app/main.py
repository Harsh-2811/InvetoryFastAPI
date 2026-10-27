from dotenv import load_dotenv
from decimal import Decimal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.routes.products import router as products_router
from app.routes.orders import router as orders_router
from app.database import lifespan

app = FastAPI(title = "Inventory and Order API", version = "1.0.0", lifespan = lifespan)

app.include_router(products_router)
app.include_router(orders_router)
@app.get("/heath")
async def heath():
    return {"status": "ok"}