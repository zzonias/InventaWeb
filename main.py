from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI(title="InventaWeb Backend")
DB_NAME = "inventaweb.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                min_stock INTEGER NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                cpf TEXT NOT NULL UNIQUE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                product_id INTEGER,
                quantity INTEGER NOT NULL,
                total REAL NOT NULL,
                sale_date TEXT NOT NULL
            )
        """)


init_db()


class Product(BaseModel):
    name: str
    price: float
    stock: int
    min_stock: int


class Customer(BaseModel):
    name: str
    email: str
    phone: str
    cpf: str


class Sale(BaseModel):
    customer_id: int
    product_id: int
    quantity: int


@app.post("/products")
def create_product(product: Product):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO products (name, price, stock, min_stock) VALUES (?, ?, ?, ?)",
            (
                product.name,
                product.price,
                product.stock,
                product.min_stock
            )
        )

    return {"message": "Produto cadastrado com sucesso"}


@app.get("/products")
def list_products():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM products")
        data = cursor.fetchall()

    return [
        {
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "stock": p[3],
            "min_stock": p[4]
        }
        for p in data
    ]


@app.get("/products/low-stock")
def low_stock_products():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM products WHERE stock <= min_stock"
        )

        data = cursor.fetchall()

    return [
        {
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "stock": p[3],
            "min_stock": p[4]
        }
        for p in data
    ]


@app.post("/customers")
def create_customer(customer: Customer):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO customers (name, email, phone, cpf)
            VALUES (?, ?, ?, ?)
            """,
            (
                customer.name,
                customer.email,
                customer.phone,
                customer.cpf
            )
        )

    return {"message": "Cliente cadastrado com sucesso"}


@app.get("/customers")
def list_customers():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM customers")
        data = cursor.fetchall()

    return [
        {
            "id": c[0],
            "name": c[1],
            "email": c[2],
            "phone": c[3],
            "cpf": c[4]
        }
        for c in data
    ]


@app.post("/sales")
def register_sale(sale: Sale):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price, stock FROM products WHERE id = ?",
            (sale.product_id,)
        )

        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado"
            )

        price, stock = product

        if stock < sale.quantity:
            raise HTTPException(
                status_code=400,
                detail="Estoque insuficiente"
            )

        total = price * sale.quantity
        new_stock = stock - sale.quantity

        cursor.execute(
            "UPDATE products SET stock = ? WHERE id = ?",
            (new_stock, sale.product_id)
        )

        cursor.execute(
            """
            INSERT INTO sales
            (customer_id, product_id, quantity, total, sale_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                sale.customer_id,
                sale.product_id,
                sale.quantity,
                total,
                datetime.now().isoformat()
            )
        )

    return {
        "message": "Venda registrada com sucesso",
        "total": total
    }


@app.get("/sales")
def list_sales():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sales")
        data = cursor.fetchall()

    return [
        {
            "id": s[0],
            "customer_id": s[1],
            "product_id": s[2],
            "quantity": s[3],
            "total": s[4],
            "sale_date": s[5]
        }
        for s in data
    ]


@app.get("/dashboard")
def dashboard():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sales")
        total_sales = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total) FROM sales")
        revenue = cursor.fetchone()[0] or 0

    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_sales": total_sales,
        "revenue": revenue
    }