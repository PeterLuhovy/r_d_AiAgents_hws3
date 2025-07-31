import os
import time

from fastapi import FastAPI, HTTPException, Body
from typing import Dict, Any, List, cast
from contextlib import asynccontextmanager
from databases import Database
from datetime import date

database: Database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global database
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sql_finance")
    database = Database(database_url)
    await database.connect()
    yield
    # Shutdown
    await database.disconnect()

app = FastAPI(title="SQL Database Manager", version="0.0.0", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "SQL database Manager API"}

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "timestamp": time.time(),
        "status": "healthy",
        "service": "database_service",
        "version": "0.1.0"
    }


@app.get("/invoices")
async def get_all_invoices() -> List[Dict[str, Any]]:
    query = "SELECT * FROM invoices ORDER BY date_created DESC"
    rows = cast(List[Dict[str, Any]], await database.fetch_all(query)) # type: ignore
    
    invoices: List[Dict[str, Any]] = []
    for row in rows:
        invoices.append({
            "id": row["id"],
            "invoice_number": row["invoice_number"],
            "supplier_name": row["supplier_name"],
            "amount": float(row["amount"]),
            "date_created": row["date_created"].isoformat(),
            "due_date": row["due_date"].isoformat()
        })
    return invoices

@app.post("/invoices")
async def create_invoice(
    invoice_number: str = Body(...),
    supplier_name: str = Body(...),
    amount: float = Body(...),
    date_created: str = Body(...),
    due_date: str = Body(...)
) -> Dict[str, Any]:
    try:
        # Convert string dates to date objects
        date_created_obj = date.fromisoformat(date_created)
        due_date_obj = date.fromisoformat(due_date)
        
        query = """
        INSERT INTO invoices (invoice_number, supplier_name, amount, date_created, due_date)
        VALUES (:invoice_number, :supplier_name, :amount, :date_created, :due_date)
        RETURNING id
        """
        
        result = await database.fetch_one(query, values={ # type: ignore
            "invoice_number": invoice_number,
            "supplier_name": supplier_name,
            "amount": amount,
            "date_created": date_created_obj,
            "due_date": due_date_obj
        })
        
        if result is None:
            raise HTTPException(status_code=500, detail="Failed to create invoice")
        
        return {
            "message": "Invoice created successfully",
            "id": result["id"],
            "invoice_number": invoice_number
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")