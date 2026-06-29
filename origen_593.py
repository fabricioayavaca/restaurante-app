from flask import Flask, render_template, request
import sqlite3
from datetime import datetime

app = Flask(__name__)

# ==========================
# BASE DE DATOS
# ==========================
def get_db():
    conexion = sqlite3.connect("restaurante.db")
    conexion.row_factory = sqlite3.Row
    return conexion

conexion = get_db()
cursor = conexion.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS ventas(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente TEXT NOT NULL,
    fecha TEXT NOT NULL,
    total REAL NOT NULL
)
""")
conexion.commit()
conexion.close()

# ==========================
# MENÚ
# ==========================
menu = {
    "Ceviche de Camaron": 6.50,
    "Tigrillo": 3.50,
    "Encebollado Tradicional": 4.00,
    "Bolon": 2.50,
    "Cuy Asado con Papas y Aji": 12.00,
    "Hornado con Mote": 8.00,
    "Churrasco": 7.50,
    "Arroz Marinero": 9.00,
    "Maito": 6.00,
    "Tonga de Pollo": 5.00,
    "Encocado de Pescado": 7.00,
    "Seco de Chivo": 8.50,
    "Caldo Bola": 5.50,
    "Locro de Papas": 4.50,
    "Caldo de Pollo": 4.00,
    "Ceviche Mixto": 7.50,
    "Agua Sin Gas": 1.00,
    "Agua Con Gas": 1.20,
    "Cafe": 1.50,
    "Jugo Mora": 2.00,
    "Limonada": 2.00,
    "Maracuya": 2.00,
    "Naranjilla": 2.00,
    "Horchata": 2.00,
    "Coca Cola": 1.50,
    "Sprite": 1.50,
    "Fanta": 1.50,
    "Canelazo": 3.00,
    "Cerveza Club": 3.50,
    "Cerveza Pilsener": 3.50,
    "Cerveza 593": 3.50,
    "Sangria": 4.00,
    "Vino": 5.00,
    "Higos con Queso": 3.00,
    "Helado de Paila": 2.50,
    "Espumilla": 2.00,
    "Pastel de Chonta": 3.50,
    "Menestra": 1.50,
    "Choclo": 1.00,
    "Maduro con Queso": 2.00,
    "Patacones": 2.00,
    "Chifles": 1.50,
    "Huevo": 0.50,
    "Papas Fritas": 2.00
}

# ==========================
# RUTAS WEB
# ==========================
@app.route("/")
def index():
    return render_template("index.html", menu=menu)

@app.route("/pedido", methods=["POST"])
def pedido():
    cliente = request.form["cliente"]
    productos = request.form.getlist("producto")
    cantidades = request.form.getlist("cantidad")

    total = 0
    detalles = []

    for producto, cantidad in zip(productos, cantidades):
        if cantidad and int(cantidad) > 0:
            subtotal = menu[producto] * int(cantidad)
            detalles.append((producto, int(cantidad), subtotal))
            total += subtotal

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ventas(cliente,fecha,total) VALUES(?,?,?)",
                   (cliente, fecha, total))
    conexion.commit()
    conexion.close()

    return render_template("factura.html", cliente=cliente, fecha=fecha, detalles=detalles, total=total)

# ✅ CORREGIDO: renombrada de index() a ventas()
@app.route("/ventas")
def ventas():
    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM ventas ORDER BY id DESC")
    registros = cursor.fetchall()
    conexion.close()

    total_general = sum([r["total"] for r in registros])

    return render_template("ventas.html", registros=registros, total_general=total_general)

# ==========================
# EJECUCIÓN
# ==========================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)