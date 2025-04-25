
# app_streamlit_facturacion.py
import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from datetime import datetime
import os

# Archivos de historial y número de factura
FACTURA_TRACKER = "factura_numero.txt"
HISTORIAL_PATH = "historial_facturas.xlsx"

# Funciones de soporte
def obtener_numero_factura():
    if not os.path.exists(FACTURA_TRACKER):
        with open(FACTURA_TRACKER, "w") as f:
            f.write("1")
    with open(FACTURA_TRACKER, "r") as f:
        return int(f.read().strip())

def incrementar_numero_factura():
    numero = obtener_numero_factura() + 1
    with open(FACTURA_TRACKER, "w") as f:
        f.write(str(numero))
    return numero

def leer_productos_excel(uploaded_file):
    df = pd.read_excel(uploaded_file, sheet_name="catalogo_productos")
    df = df[["Codigo", "descripcion", "precio", "Imagen"]]
    df.columns = ["codigo", "descripcion", "precio", "imagen"]
    return df.to_dict(orient="records")

def guardar_historial(factura_data):
    df_nuevo = pd.DataFrame([factura_data])
    if os.path.exists(HISTORIAL_PATH):
        df_existente = pd.read_excel(HISTORIAL_PATH)
        df_final = pd.concat([df_existente, df_nuevo], ignore_index=True)
    else:
        df_final = df_nuevo
    df_final.to_excel(HISTORIAL_PATH, index=False)

def generar_pdf(nombre, celular, direccion, proveedor, carrito, total):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(30, 750, f"Factura No: {obtener_numero_factura()}")
    c.drawString(30, 735, f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c.drawString(30, 720, f"Cliente: {nombre}")
    c.drawString(30, 705, f"Celular: {celular}")
    c.drawString(30, 690, f"Direccion: {direccion}")
    c.drawString(30, 675, f"Proveedor: {proveedor}")

    c.drawString(30, 645, "Productos:")
    y = 630
    for item in carrito:
        c.drawString(40, y, f"{item['cantidad']}x {item['descripcion']} - C${item['precio']:.2f}")
        y -= 15

    subtotal = round(total / 1.15, 2)
    iva = round(total - subtotal, 2)
    c.drawString(30, y-10, f"Subtotal: C${subtotal:.2f}")
    c.drawString(30, y-25, f"IVA: C${iva:.2f}")
    c.drawString(30, y-40, f"Total: C${total:.2f}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- Streamlit App ---
st.set_page_config(page_title="Panda Facturación", layout="centered")
st.image("https://i.imgur.com/NZFZZvD.jpeg", width=150)
st.title("Facturación Digital - Panda App")

menu = st.sidebar.selectbox("Menú", ["Crear Factura", "Historial"])

# Datos de proveedores
proveedores_info = {
    'Panda Store': 'https://i.imgur.com/NZFZZvD.png',
    'Cargotrans': 'https://i.imgur.com/BdIHbRs.png',
    'PedidosYa': 'https://i.imgur.com/KxhxMwF.png'
}

if menu == "Crear Factura":
    st.subheader("📄 Crear Factura")
    uploaded_file = st.file_uploader("Sube tu archivo Excel de productos", type=["xlsx"])
    if uploaded_file:
        productos = leer_productos_excel(uploaded_file)
        nombre = st.text_input("Nombre del Cliente")
        celular = st.text_input("Celular")
        direccion = st.text_input("Dirección")

        proveedor = st.selectbox("Selecciona el proveedor", list(proveedores_info.keys()))
        st.image(proveedores_info[proveedor], width=150)

        texto_buscar = st.text_input("Buscar producto")
        productos_filtrados = [p for p in productos if texto_buscar.lower() in p['descripcion'].lower()]

        carrito = []
        total = 0

        for p in productos_filtrados:
            with st.expander(p['descripcion']):
                st.image(p['imagen'], width=150)
                st.write(f"Precio: C${p['precio']:.2f}")
                cantidad = st.number_input(f"Cantidad - {p['descripcion']}", min_value=0, step=1, key=p['codigo'])
                if cantidad > 0:
                    subtotal = p['precio'] * cantidad
                    total += subtotal
                    carrito.append({"descripcion": p['descripcion'], "cantidad": cantidad, "precio": p['precio']})

        if carrito:
            subtotal = round(total / 1.15, 2)
            iva = round(total - subtotal, 2)
            st.info(f"Subtotal: C${subtotal:.2f} | IVA: C${iva:.2f} | Total: C${total:.2f}")

            if st.button("Generar Factura en PDF"):
                pdf = generar_pdf(nombre, celular, direccion, proveedor, carrito, total)
                incrementar_numero_factura()
                factura_data = {
                    "Factura": obtener_numero_factura()-1,
                    "Fecha": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Cliente": nombre,
                    "Teléfono": celular,
                    "Dirección": direccion,
                    "Total": total
                }
                guardar_historial(factura_data)
                st.success("Factura generada con éxito!")
                st.download_button("Descargar Factura PDF", pdf, file_name="factura.pdf")

elif menu == "Historial":
    st.subheader("📚 Historial de Facturas")
    if os.path.exists(HISTORIAL_PATH):
        df = pd.read_excel(HISTORIAL_PATH)
        st.dataframe(df, use_container_width=True)
        st.download_button("Descargar historial completo", df.to_excel(index=False), file_name="historial_facturas.xlsx")
    else:
        st.warning("Aún no hay historial disponible.")
