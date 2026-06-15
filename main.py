from fastapi import FastAPI, HTTPException, Response, Header
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import random
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.graphics.barcode import createBarcodeDrawing

app = FastAPI(title="InventaWeb Backend")
DB_NAME = "inventaweb.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                store_name TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL,
                min_stock INTEGER NOT NULL,
                barcode TEXT
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
                sale_date TEXT NOT NULL,
                source TEXT DEFAULT 'Presencial',
                invoice_key TEXT
            )
        """)

        # Migração automática
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'barcode' not in columns:
            cursor.execute("ALTER TABLE products ADD COLUMN barcode TEXT")

        cursor.execute("PRAGMA table_info(sales)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'source' not in columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN source TEXT DEFAULT 'Presencial'")
        if 'invoice_key' not in columns:
            cursor.execute("ALTER TABLE sales ADD COLUMN invoice_key TEXT")

        # Migração do store_id para isolamento multi-loja
        for table in ['products', 'customers', 'sales']:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [col[1] for col in cursor.fetchall()]
            if 'store_id' not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN store_id INTEGER DEFAULT 1")


init_db()


def generate_ean13():
    digits = [7, 8, 9] + [random.randint(0, 9) for _ in range(9)]
    odd_sum = sum(digits[i] for i in range(0, 12, 2))
    even_sum = sum(digits[i] for i in range(1, 12, 2))
    total = odd_sum + (even_sum * 3)
    checksum = (10 - (total % 10)) % 10
    return "".join(map(str, digits)) + str(checksum)


def generate_invoice_key():
    return "".join(str(random.randint(0, 9)) for _ in range(44))


class UserRegister(BaseModel):
    username: str
    password: str
    store_name: str


class UserLogin(BaseModel):
    username: str
    password: str


@app.post("/auth/register")
def register_user(user: UserRegister):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, store_name) VALUES (?, ?, ?)",
                (user.username, user.password, user.store_name)
            )
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Usuário já cadastrado.")
    return {"message": "Usuário registrado com sucesso", "store_id": user_id, "store_name": user.store_name}


@app.post("/auth/login")
def login_user(user: UserLogin):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, store_name, password FROM users WHERE username = ?", (user.username,))
        row = cursor.fetchone()
        if not row or row[2] != user.password:
            raise HTTPException(status_code=401, detail="Usuário ou senha incorretos.")
    return {"message": "Sucesso", "store_id": row[0], "store_name": row[1]}


class Product(BaseModel):
    name: str
    price: float
    stock: int
    min_stock: int
    barcode: str = None


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
def create_product(product: Product, x_store_id: int = Header(1, alias="X-Store-ID")):
    barcode = product.barcode
    if not barcode or not barcode.strip():
        barcode = generate_ean13()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO products (name, price, stock, min_stock, barcode, store_id) VALUES (?, ?, ?, ?, ?, ?)",
            (
                product.name,
                product.price,
                product.stock,
                product.min_stock,
                barcode,
                x_store_id
            )
        )

    return {"message": "Produto cadastrado com sucesso", "barcode": barcode}


@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product, x_store_id: int = Header(1, alias="X-Store-ID")):
    barcode = product.barcode
    if not barcode or not barcode.strip():
        barcode = generate_ean13()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM products WHERE id = ? AND store_id = ?", (product_id, x_store_id))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado nesta loja"
            )

        cursor.execute(
            """
            UPDATE products 
            SET name = ?, price = ?, stock = ?, min_stock = ?, barcode = ?
            WHERE id = ? AND store_id = ?
            """,
            (
                product.name,
                product.price,
                product.stock,
                product.min_stock,
                barcode,
                product_id,
                x_store_id
            )
        )

    return {"message": "Produto atualizado com sucesso"}


@app.get("/products")
def list_products(x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, price, stock, min_stock, barcode FROM products WHERE store_id = ?", (x_store_id,))
        data = cursor.fetchall()

    return [
        {
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "stock": p[3],
            "min_stock": p[4],
            "barcode": p[5] or ""
        }
        for p in data
    ]


@app.get("/products/low-stock")
def low_stock_products(x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, price, stock, min_stock, barcode FROM products WHERE stock <= min_stock AND store_id = ?",
            (x_store_id,)
        )

        data = cursor.fetchall()

    return [
        {
            "id": p[0],
            "name": p[1],
            "price": p[2],
            "stock": p[3],
            "min_stock": p[4],
            "barcode": p[5] or ""
        }
        for p in data
    ]



@app.post("/customers")
def create_customer(customer: Customer, x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO customers (name, email, phone, cpf, store_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    customer.name,
                    customer.email,
                    customer.phone,
                    customer.cpf,
                    x_store_id
                )
            )
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    return {"message": "Cliente cadastrado com sucesso"}


@app.get("/customers")
def list_customers(x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, email, phone, cpf FROM customers WHERE store_id = ?", (x_store_id,))
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
def register_sale(sale: Sale, x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price, stock FROM products WHERE id = ? AND store_id = ?",
            (sale.product_id, x_store_id)
        )

        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado nesta loja"
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
            "UPDATE products SET stock = ? WHERE id = ? AND store_id = ?",
            (new_stock, sale.product_id, x_store_id)
        )


        invoice_key = generate_invoice_key()
        cursor.execute(
            """
            INSERT INTO sales
            (customer_id, product_id, quantity, total, sale_date, source, invoice_key, store_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sale.customer_id,
                sale.product_id,
                sale.quantity,
                total,
                datetime.now().isoformat(),
                "Presencial",
                invoice_key,
                x_store_id
            )
        )

    return {
        "message": "Venda registrada com sucesso",
        "total": total
    }


class MLSale(BaseModel):
    product_id: int
    quantity: int


@app.post("/mercadolivre/webhook")
def mercadolivre_webhook(ml_sale: MLSale, x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT price, stock FROM products WHERE id = ? AND store_id = ?",
            (ml_sale.product_id, x_store_id)
        )

        product = cursor.fetchone()

        if not product:
            raise HTTPException(
                status_code=404,
                detail="Produto não encontrado nesta loja"
            )

        price, stock = product

        if stock < ml_sale.quantity:
            raise HTTPException(
                status_code=400,
                detail="Estoque insuficiente no Mercado Livre"
            )

        total = price * ml_sale.quantity
        new_stock = stock - ml_sale.quantity

        cursor.execute(
            "UPDATE products SET stock = ? WHERE id = ? AND store_id = ?",
            (new_stock, ml_sale.product_id, x_store_id)
        )

        invoice_key = generate_invoice_key()
        cursor.execute(
            """
            INSERT INTO sales
            (customer_id, product_id, quantity, total, sale_date, source, invoice_key, store_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                None,
                ml_sale.product_id,
                ml_sale.quantity,
                total,
                datetime.now().isoformat(),
                "Mercado Livre",
                invoice_key,
                x_store_id
            )
        )

    return {
        "message": "Venda do Mercado Livre sincronizada com sucesso",
        "total": total
    }


@app.get("/sales")
def list_sales(x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, customer_id, product_id, quantity, total, sale_date, source, invoice_key FROM sales WHERE store_id = ?", (x_store_id,))
        data = cursor.fetchall()

    return [
        {
            "id": s[0],
            "customer_id": s[1],
            "product_id": s[2],
            "quantity": s[3],
            "total": s[4],
            "sale_date": s[5],
            "source": s[6] or "Presencial",
            "invoice_key": s[7] or ""
        }
        for s in data
    ]


@app.get("/sales/{sale_id}/pdf")
def get_sale_pdf(sale_id: int, x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.id, s.quantity, s.total, s.sale_date, s.source, s.invoice_key,
                   p.name, p.price, p.barcode
            FROM sales s
            JOIN products p ON s.product_id = p.id
            WHERE s.id = ? AND s.store_id = ?
        """, (sale_id, x_store_id))

        sale = cursor.fetchone()
        if not sale:
            raise HTTPException(status_code=404, detail="Venda não encontrada")

        sid, sqty, stotal, sdate, ssource, skey, pname, pprice, pbarcode = sale

        customer_name = "Consumidor Não Identificado"
        customer_cpf = "000.000.000-00"

        cursor.execute("SELECT customer_id FROM sales WHERE id = ?", (sale_id,))
        cid = cursor.fetchone()[0]
        if cid:
            cursor.execute("SELECT name, cpf FROM customers WHERE id = ? AND store_id = ?", (cid, x_store_id))
            cust = cursor.fetchone()
            if cust:
                customer_name, customer_cpf = cust

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    style_normal = styles['Normal']
    style_title = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#1e293b")
    )
    style_subtitle = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#64748b")
    )
    style_header = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#0f172a")
    )
    style_body = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    style_body_bold = ParagraphStyle(
        'BodyBoldStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    story.append(Paragraph("INVENTAWEB COMERCIO LTDA", style_title))
    story.append(Paragraph("CNPJ: 12.345.678/0001-90 | IE: 123.456.789.110", style_subtitle))
    story.append(Paragraph("Av. Paulista, 1000 - Bela Vista, São Paulo - SP, 01310-100", style_subtitle))
    story.append(Spacer(1, 10))
    story.append(Paragraph("DOCUMENTO AUXILIAR DA NOTA FISCAL DE CONSUMIDOR ELETRÔNICA (NFC-e)", style_body_bold))
    story.append(Spacer(1, 12))

    try:
        dt_formatted = datetime.fromisoformat(sdate).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        dt_formatted = sdate

    info_data = [
        [Paragraph("<b>Documento Nº:</b>", style_body), Paragraph(f"000.00{sid}", style_body),
         Paragraph("<b>Data/Hora Emissão:</b>", style_body), Paragraph(dt_formatted, style_body)],
        [Paragraph("<b>Origem da Venda:</b>", style_body), Paragraph(ssource, style_body),
         Paragraph("<b>Meio de Pagamento:</b>", style_body), Paragraph("Simulado", style_body)]
    ]
    t_info = Table(info_data, colWidths=[110, 140, 110, 180])
    t_info.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>DADOS DO CONSUMIDOR</b>", style_header))
    cust_data = [
        [Paragraph("<b>Nome:</b>", style_body), Paragraph(customer_name, style_body)],
        [Paragraph("<b>CPF:</b>", style_body), Paragraph(customer_cpf, style_body)]
    ]
    t_cust = Table(cust_data, colWidths=[60, 480])
    t_cust.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,-1), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
    ]))
    story.append(t_cust)
    story.append(Spacer(1, 12))

    story.append(Paragraph("<b>DETALHE DOS ITENS VENDIDOS</b>", style_header))
    prod_header = [Paragraph("<b>Item</b>", style_body_bold), Paragraph("<b>Código / Descrição</b>", style_body_bold), Paragraph("<b>Qtd.</b>", style_body_bold), Paragraph("<b>Vl. Unit. (R$)</b>", style_body_bold), Paragraph("<b>Vl. Total (R$)</b>", style_body_bold)]
    prod_rows = [
        [
            Paragraph("001", style_body),
            Paragraph(f"Código: {pbarcode or 'N/A'}<br/>{pname}", style_body),
            Paragraph(str(sqty), style_body),
            Paragraph(f"{pprice:.2f}", style_body),
            Paragraph(f"{stotal:.2f}", style_body)
        ]
    ]
    t_prod_data = [prod_header] + prod_rows
    t_prod = Table(t_prod_data, colWidths=[40, 260, 50, 90, 100])
    t_prod.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f8fafc")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor("#94a3b8")),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(t_prod)
    story.append(Spacer(1, 12))

    summary_data = [
        [Paragraph("<b>Qtd. Total de Itens:</b>", style_body), Paragraph(str(sqty), style_body)],
        [Paragraph("<b>Valor Total Consumidor (R$):</b>", style_body_bold), Paragraph(f"<b>{stotal:.2f}</b>", style_body_bold)]
    ]
    t_sum = Table(summary_data, colWidths=[200, 340])
    t_sum.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 16))

    story.append(Paragraph("<b>CHAVE DE ACESSO DA NF-e</b>", style_header))
    formatted_key = " ".join([skey[i:i+4] for i in range(0, len(skey), 4)]) if skey else "N/A"
    story.append(Paragraph(formatted_key, style_body_bold))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Consulta via leitor de QR Code ou Chave de Acesso no portal da SEFAZ.", style_subtitle))
    story.append(Spacer(1, 14))

    if pbarcode and pbarcode.isdigit() and len(pbarcode) == 13:
        try:
            barcode_drawing = createBarcodeDrawing('EAN13', value=pbarcode, barHeight=40, barWidth=1.2, fontSize=9)
            story.append(barcode_drawing)
        except Exception:
            pass

    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=nfe_venda_{sale_id}.pdf"
        }
    )


@app.get("/dashboard")
def dashboard(x_store_id: int = Header(1, alias="X-Store-ID")):
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM products WHERE store_id = ?", (x_store_id,))
        total_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM customers WHERE store_id = ?", (x_store_id,))
        total_customers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sales WHERE store_id = ?", (x_store_id,))
        total_sales = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total) FROM sales WHERE store_id = ?", (x_store_id,))
        revenue = cursor.fetchone()[0] or 0

    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_sales": total_sales,
        "revenue": revenue
    }