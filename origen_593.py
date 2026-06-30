from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime, timezone, timedelta
import os
import requests

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave-secreta-cambiar-en-produccion")

# ==========================
# CONFIGURACIÓN
# ==========================
EMAIL_REMITENTE = os.environ.get("EMAIL_REMITENTE", "tucorreo@gmail.com")
CLAVE_MESERO = os.environ.get("CLAVE_MESERO", "1234")

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
    correo TEXT,
    fecha TEXT NOT NULL,
    total REAL NOT NULL
)
""")
try:
    cursor.execute("ALTER TABLE ventas ADD COLUMN correo TEXT")
except:
    pass
conexion.commit()
conexion.close()

# ==========================
# MENÚ ORGANIZADO POR SECCIONES
# ==========================
menu_secciones = {
    "🍽️ Platos Fuertes": {
        "Cuy Asado con Papas y Aji": 12.00,
        "Hornado con Mote": 8.00,
        "Churrasco": 7.50,
        "Arroz Marinero": 9.00,
        "Maito": 6.00,
        "Tonga de Pollo": 5.00,
        "Encocado de Pescado": 7.00,
        "Seco de Chivo": 8.50,
    },
    "🥣 Entradas y Sopas": {
        "Ceviche de Camaron": 6.50,
        "Ceviche Mixto": 7.50,
        "Tigrillo": 3.50,
        "Encebollado Tradicional": 4.00,
        "Bolon": 2.50,
        "Caldo Bola": 5.50,
        "Locro de Papas": 4.50,
        "Caldo de Pollo": 4.00,
    },
    "🍟 Acompañamientos": {
        "Menestra": 1.50,
        "Choclo": 1.00,
        "Maduro con Queso": 2.00,
        "Patacones": 2.00,
        "Chifles": 1.50,
        "Huevo": 0.50,
        "Papas Fritas": 2.00,
    },
    "🍮 Postres": {
        "Higos con Queso": 3.00,
        "Helado de Paila": 2.50,
        "Espumilla": 2.00,
        "Pastel de Chonta": 3.50,
    },
    "🥤 Bebidas": {
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
    },
}

menu = {producto: precio
        for seccion in menu_secciones.values()
        for producto, precio in seccion.items()}

# ==========================
# FUNCIÓN ENVIAR CORREO (Brevo)
# ==========================
def enviar_factura_email(correo_destino, cliente, fecha, detalles, total):
    try:
        filas = ""
        for producto, cantidad, subtotal in detalles:
            filas += f"""
            <tr>
                <td style="padding:8px 12px;border-bottom:1px solid #f0ebe3;">{producto}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #f0ebe3;text-align:center;">{cantidad}</td>
                <td style="padding:8px 12px;border-bottom:1px solid #f0ebe3;text-align:right;">${subtotal:.2f}</td>
            </tr>"""

        html = f"""
        <html><body style="font-family:Georgia,serif;background:#fdf6ee;margin:0;padding:20px;">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.1);">
            <div style="background:#8B0000;color:white;padding:24px;text-align:center;">
                <h1 style="margin:0;font-size:1.5em;letter-spacing:1px;">Factura</h1>
                <p style="margin:4px 0 0;opacity:0.8;font-style:italic;">Restaurante 593 - Sabores del Ecuador</p>
            </div>
            <div style="padding:28px;">
                <p style="color:#555;margin-bottom:6px;"><strong>Cliente:</strong> {cliente}</p>
                <p style="color:#555;margin-bottom:20px;"><strong>Fecha:</strong> {fecha}</p>
                <h2 style="color:#8B0000;font-size:1em;text-transform:uppercase;letter-spacing:1px;
                           margin-bottom:12px;border-bottom:2px solid #8B0000;padding-bottom:8px;">
                    Detalle del pedido
                </h2>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#8B0000;color:white;">
                            <th style="padding:10px 12px;text-align:left;font-size:0.82em;">Producto</th>
                            <th style="padding:10px 12px;text-align:center;font-size:0.82em;">Cant.</th>
                            <th style="padding:10px 12px;text-align:right;font-size:0.82em;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>{filas}</tbody>
                    <tfoot>
                        <tr style="background:#fff8f3;">
                            <td colspan="2" style="padding:12px;font-weight:bold;color:#8B0000;
                                border-top:2px solid #8B0000;">TOTAL</td>
                            <td style="padding:12px;font-weight:bold;color:#8B0000;text-align:right;
                                border-top:2px solid #8B0000;">${total:.2f}</td>
                        </tr>
                    </tfoot>
                </table>
                <p style="margin-top:24px;color:#999;font-size:0.82em;text-align:center;
                          font-family:Arial,sans-serif;">
                    Gracias por tu pedido - Restaurante 593
                </p>
            </div>
        </div>
        </body></html>"""

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": os.environ.get("BREVO_API_KEY", ""),
                "Content-Type": "application/json"
            },
            json={
                "sender": {"name": "Restaurante 593", "email": EMAIL_REMITENTE},
                "to": [{"email": correo_destino}],
                "subject": f"Tu factura de Restaurante 593 - {fecha}",
                "htmlContent": html
            }
        )
        print(f"Brevo response: {response.status_code} - {response.text}")
        return response.status_code == 201
    except Exception as e:
        print(f"Error al enviar correo: {e}")
        return False

# ==========================
# RUTAS WEB
# ==========================

# Página de bienvenida (Cliente / Mesero)
@app.route("/")
def bienvenida():
    return render_template("bienvenida.html")

# Verifica la clave del mesero
@app.route("/verificar-mesero")
def verificar_mesero():
    clave = request.args.get("clave", "")
    if clave == CLAVE_MESERO:
        session["es_mesero"] = True
        return redirect("/ventas")
    return redirect("/?error=1")

# Menú para clientes (cierra sesión de mesero si la hubiera)
@app.route("/menu")
def index():
    if request.args.get("salir") == "1":
        session.pop("es_mesero", None)
    es_mesero = session.get("es_mesero", False)
    return render_template("index.html", menu_secciones=menu_secciones, es_mesero=es_mesero)

@app.route("/pedido", methods=["POST"])
def pedido():
    cliente = request.form["cliente"]
    correo  = request.form.get("correo", "")
    productos = request.form.getlist("producto")
    cantidades = request.form.getlist("cantidad")

    total = 0
    detalles = []

    for producto, cantidad in zip(productos, cantidades):
        if cantidad and int(cantidad) > 0:
            subtotal = menu[producto] * int(cantidad)
            detalles.append((producto, int(cantidad), subtotal))
            total += subtotal

    zona_ecuador = timezone(timedelta(hours=-5))
    fecha = datetime.now(zona_ecuador).strftime("%d/%m/%Y %H:%M:%S")

    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("INSERT INTO ventas(cliente, correo, fecha, total) VALUES(?,?,?,?)",
                   (cliente, correo, fecha, total))
    conexion.commit()
    conexion.close()

    email_enviado = False
    if correo and detalles:
        email_enviado = enviar_factura_email(correo, cliente, fecha, detalles, total)

    return render_template("factura.html",
                           cliente=cliente,
                           correo=correo,
                           fecha=fecha,
                           detalles=detalles,
                           total=total,
                           email_enviado=email_enviado)

# Historial de ventas — solo accesible si pasó por la clave de mesero
@app.route("/ventas")
def ventas():
    if not session.get("es_mesero"):
        return redirect("/")

    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM ventas ORDER BY id DESC")
    registros = cursor.fetchall()
    conexion.close()

    total_general = sum([r["total"] for r in registros])

    return render_template("ventas.html", registros=registros, total_general=total_general)

# Eliminar una venta (solo mesero)
@app.route("/eliminar-venta/<int:venta_id>", methods=["POST"])
def eliminar_venta(venta_id):
    if not session.get("es_mesero"):
        return jsonify({"exito": False}), 403

    conexion = get_db()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))
    conexion.commit()
    conexion.close()

    return jsonify({"exito": True})

# ==========================
# EJECUCIÓN
# ==========================
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
