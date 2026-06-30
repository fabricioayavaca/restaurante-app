"""RESTAURANTE 593 - Estructura principal (resumen demostrativo)"""

from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3, requests
from datetime import datetime

app = Flask(__name__)
CLAVE_MESERO = "1234"

# ==========================
# MENÚ DEL RESTAURANTE
# ==========================
menu_secciones = {
    "Platos Fuertes": {"Hornado": 8.00, "Churrasco": 7.50},
    "Bebidas": {"Jugo": 2.00, "Cerveza": 3.50},
}
menu = {p: pr for s in menu_secciones.values() for p, pr in s.items()}


# ==========================
# PANTALLA DE BIENVENIDA
# Permite elegir entre Cliente o Mesero
# ==========================
@app.route("/")
def bienvenida():
    return render_template("bienvenida.html")


# ==========================
# VERIFICA LA CLAVE DEL MESERO
# Si es correcta, da acceso al historial de ventas
# ==========================
@app.route("/verificar-mesero")
def verificar_mesero():
    if request.args.get("clave") == CLAVE_MESERO:
        session["es_mesero"] = True
        return redirect("/ventas")
    return redirect("/")


# ==========================
# MUESTRA EL MENÚ AL CLIENTE
# ==========================
@app.route("/menu")
def menu_view():
    return render_template("index.html", menu_secciones=menu_secciones)


# ==========================
# REGISTRA EL PEDIDO
# Calcula el total, guarda en la base de datos
# y envía la factura por correo
# ==========================
@app.route("/pedido", methods=["POST"])
def pedido():
    cliente = request.form["cliente"]
    correo = request.form.get("correo")
    detalles, total = [], 0

    for producto, cantidad in zip(request.form.getlist("producto"),
                                   request.form.getlist("cantidad")):
        if int(cantidad) > 0:
            subtotal = menu[producto] * int(cantidad)
            detalles.append((producto, cantidad, subtotal))
            total += subtotal

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Guardar venta en la base de datos
    db = sqlite3.connect("restaurante.db")
    db.execute("INSERT INTO ventas VALUES(?,?,?,?)", (cliente, correo, fecha, total))
    db.commit()

    # Enviar factura por correo (API Brevo)
    requests.post("https://api.brevo.com/v3/smtp/email", json={
        "to": [{"email": correo}], "subject": "Factura Restaurante 593"
    })

    return render_template("factura.html", cliente=cliente, fecha=fecha,
                            detalles=detalles, total=total)


# ==========================
# HISTORIAL DE VENTAS
# Solo accesible si el usuario inició sesión como mesero
# ==========================
@app.route("/ventas")
def ventas():
    if not session.get("es_mesero"):
        return redirect("/")
    registros = sqlite3.connect("restaurante.db").execute("SELECT * FROM ventas").fetchall()
    return render_template("ventas.html", registros=registros)


# ==========================
# ELIMINA UN REGISTRO DE VENTA
# ==========================
@app.route("/eliminar-venta/<int:id>", methods=["POST"])
def eliminar_venta(id):
    sqlite3.connect("restaurante.db").execute("DELETE FROM ventas WHERE id=?", (id,))
    return jsonify({"exito": True})


# ==========================
# EJECUCIÓN DEL SERVIDOR
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
