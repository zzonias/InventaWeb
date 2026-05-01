from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI(title="InventaWeb Backend")
DB_NAME = "inventaweb.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
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
            email TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            total REAL NOT NULL,
            sale_date TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


class Product(BaseModel):
    name: str
    price: float
    stock: int
    min_stock: int


class Customer(BaseModel):
    name: str
    email: str


class Sale(BaseModel):
    customer_id: int
    product_id: int
    quantity: int


@app.post("/products")
def create_product(product: Product):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO products (name, price, stock, min_stock) VALUES (?, ?, ?, ?)",
        (product.name, product.price, product.stock, product.min_stock)
    )

    conn.commit()
    conn.close()

    return {"message": "Produto cadastrado com sucesso"}


@app.get("/products")
def list_products():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    data = cursor.fetchall()

    conn.close()
    return data


@app.get("/products/low-stock")
def low_stock_products():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products WHERE stock <= min_stock")
    data = cursor.fetchall()

    conn.close()
    return data


@app.post("/customers")
def create_customer(customer: Customer):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO customers (name, email) VALUES (?, ?)",
        (customer.name, customer.email)
    )

    conn.commit()
    conn.close()

    return {"message": "Cliente cadastrado com sucesso"}


@app.get("/customers")
def list_customers():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM customers")
    data = cursor.fetchall()

    conn.close()
    return data


@app.post("/sales")
def register_sale(sale: Sale):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT price, stock FROM products WHERE id = ?",
        (sale.product_id,)
    )

    product = cursor.fetchone()

    if not product:
        conn.close()
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    price, stock = product

    if stock < sale.quantity:
        conn.close()
        raise HTTPException(status_code=400, detail="Estoque insuficiente")

    total = price * sale.quantity
    new_stock = stock - sale.quantity

    cursor.execute(
        "UPDATE products SET stock = ? WHERE id = ?",
        (new_stock, sale.product_id)
    )

    cursor.execute(
        "INSERT INTO sales (customer_id, product_id, quantity, total, sale_date) VALUES (?, ?, ?, ?, ?)",
        (
            sale.customer_id,
            sale.product_id,
            sale.quantity,
            total,
            datetime.now().isoformat()
        )
    )

    conn.commit()
    conn.close()

    return {
        "message": "Venda registrada com sucesso",
        "total": total
    }


@app.get("/sales")
def list_sales():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sales")
    data = cursor.fetchall()

    conn.close()
    return data


@app.get("/dashboard")
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total) FROM sales")
    revenue = cursor.fetchone()[0] or 0

    conn.close()

    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_sales": total_sales,
        "revenue": revenue
    }