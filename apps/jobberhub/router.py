from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
import psycopg2.extras
import os

router = APIRouter(tags=["JobberHub"])

DB_URL = os.getenv("FLEMING_DB_URL", "dbname=fleming_db user=fleming_user password=fl3m1ng_db_2026! host=localhost")


def get_conn():
    return psycopg2.connect(DB_URL)


# --- Categories ---

@router.get("/jobberhub/categories")
async def list_categories():
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM categories ORDER BY name")
        return cur.fetchall()
    finally:
        conn.close()


# --- Suppliers ---

class SupplierModel(BaseModel):
    name: str
    zip_code: Optional[str] = None
    rating: Optional[float] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None


@router.get("/jobberhub/suppliers")
async def list_suppliers():
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM suppliers ORDER BY name")
        return cur.fetchall()
    finally:
        conn.close()


@router.get("/jobberhub/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return row
    finally:
        conn.close()


@router.post("/jobberhub/suppliers")
async def create_supplier(s: SupplierModel):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO suppliers (name, zip_code, rating, email, phone, bio) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
            (s.name, s.zip_code, s.rating, s.email, s.phone, s.bio)
        )
        sid = cur.fetchone()[0]
        conn.commit()
        return {"id": sid, "status": "created"}
    finally:
        conn.close()


@router.put("/jobberhub/suppliers/{supplier_id}")
async def update_supplier(supplier_id: int, s: SupplierModel):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE suppliers SET name=%s, zip_code=%s, rating=%s, email=%s, phone=%s, bio=%s, updated_at=NOW() WHERE id=%s",
            (s.name, s.zip_code, s.rating, s.email, s.phone, s.bio, supplier_id)
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return {"status": "updated"}
    finally:
        conn.close()


# --- Products ---

class ProductModel(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    sku: Optional[str] = None
    stock_quantity: Optional[int] = 0
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None


@router.get("/jobberhub/products")
async def list_products(category_id: Optional[int] = None, search: Optional[str] = None, limit: int = 20):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            SELECT p.*, s.name as supplier_name, s.zip_code as supplier_zip, s.rating as supplier_rating
            FROM products p
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE 1=1
        """
        params = []
        if category_id:
            query += " AND p.category_id = %s"
            params.append(category_id)
        if search:
            query += " AND p.name ILIKE %s"
            params.append(f"%{search}%")
        query += " ORDER BY p.name LIMIT %s"
        params.append(limit)
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()


@router.post("/jobberhub/products")
async def create_product(p: ProductModel):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO products (name, description, price, sku, stock_quantity, category_id, supplier_id) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
            (p.name, p.description, p.price, p.sku, p.stock_quantity, p.category_id, p.supplier_id)
        )
        pid = cur.fetchone()[0]
        conn.commit()
        return {"id": pid, "status": "created"}
    finally:
        conn.close()


@router.post("/jobberhub/products/bulk")
async def bulk_create_products(products: list[ProductModel]):
    conn = get_conn()
    try:
        cur = conn.cursor()
        ids = []
        for p in products:
            cur.execute(
                "INSERT INTO products (name, description, price, sku, stock_quantity, category_id, supplier_id) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id",
                (p.name, p.description, p.price, p.sku, p.stock_quantity, p.category_id, p.supplier_id)
            )
            ids.append(cur.fetchone()[0])
        conn.commit()
        return {"ids": ids, "count": len(ids), "status": "created"}
    finally:
        conn.close()
