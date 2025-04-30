
# app_streamlit_facturacion_actualizado.py
import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
import os
import pytz
from textwrap import wrap
from PIL import Image
import requests


FACTURA_TRACKER = "factura_numero.txt"
HISTORIAL_PATH = "historial_facturas.xlsx"

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

def generar_pdf(nombre, celular, direccion, proveedor, carrito, total, subtotal, iva):

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # Registrar fuente Calibri
    pdfmetrics.registerFont(TTFont('Calibri', 'calibri.ttf'))
    pdfmetrics.registerFont(TTFont('Calibri-Bold', 'Calibri-Bold.ttf'))

    # Encabezado
    c.setFillColorRGB(0.93, 0.93, 0.93)
    c.roundRect(30, 700, 530, 60, 10, fill=1)

    try:
        c.drawImage("pandastore.jpg", 500, 710, width=45, height=40, mask='auto')
    except:
        pass

    c.setFont("Calibri-Bold", 18)
    c.setFillColor(colors.darkblue)
    c.drawCentredString(295, 735, "Panda Store")

    c.setFont("Calibri-Bold", 10)
    c.setFillColor(colors.gray)
    c.drawCentredString(295, 720, "Factura Comercial")

    c.setFillColor(colors.black)
    tz = pytz.timezone('America/Managua')
    now = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    factura_no = obtener_numero_factura()

    c.setFont("Calibri-Bold", 10)
    c.drawString(30, 685, f"Factura No: {factura_no}")
    c.drawRightString(560, 685, f"Fecha: {now}")

    # Cuadros
    c.setFillColorRGB(0.8, 0.9, 1)
    c.roundRect(30, 610, 250, 70, 5, fill=1)
    c.roundRect(310, 610, 250, 70, 5, fill=1)

    c.setFillColor(colors.black)
    c.setFont("Calibri-Bold", 9)
    c.drawString(40, 670, "Facturado Por:")
    c.setFont("Calibri", 8)
    c.drawString(40, 660, "Panda Store")
    c.drawString(40, 650, "Reparto San Juan, Managua")
    c.drawString(40, 640, "pandastorenic@gmail.com")
    c.drawString(40, 630, "+505 8372 5528")

    c.setFont("Calibri-Bold", 9)
    c.drawString(320, 670, "Facturado A:")
    c.setFont("Calibri", 8)
    
    direccion_lines = wrap(direccion, 60)
    linea_actual = 660
    altura_cuadro_cliente = 70
    espacio_minimo = 20
    
    # Escribir nombre
    c.drawString(320, linea_actual, nombre)
    
    # Escribir cada línea de la dirección
    for line in direccion_lines:
        linea_actual -= 10
        c.drawString(320, linea_actual, line)
    
    # Escribir celular
    linea_actual -= 10
    c.drawString(320, linea_actual, celular)
    
    # Escribir proveedor
    linea_actual -= 10
    c.drawString(320, linea_actual, f"Proveedor: {proveedor}")

    # Tabla productos
    direccion_lines = len(direccion_lines)
    y_tabla = 610 - altura_cuadro_cliente - (direccion_lines * 10) - espacio_minimo
    table_data = [["Id", "Descripción", "IVA %", "Cantidad", "Precio\nUnitario", "Descuento\n(C$)", "Monto\nsin IVA", "IVA\n(C$)", "Monto\nTotal"]]
    
    for idx, item in enumerate(carrito, start=1):
        monto_sin_iva = item['total_linea'] / 1.15
        iva_c = item['total_linea'] - monto_sin_iva
    
        descripcion_wrapped = "\n".join(wrap(item['descripcion'], 25))
    
        table_data.append([
            str(idx),
            descripcion_wrapped,
            "15%",
            str(item['cantidad']),
            f"C${item['precio']:.2f}",
            f"C${item['descuento']:.2f}",
            f"C${monto_sin_iva:.2f}",
            f"C${iva_c:.2f}",
            f"C${item['total_linea']:.2f}"
        ])
    
    # Definimos tabla
    table = Table(table_data, colWidths=[25, 155, 35, 35, 55, 55, 65, 50, 65])
    
    # Aplicamos estilo
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Calibri-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),  # <-- Reducción de fuente en encabezado
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('FONTNAME', (0,1), (-1,-1), 'Calibri'),
        ('FONTSIZE', (0,1), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    
    # Dibujamos la tabla
    table.wrapOn(c, 30, y_tabla)
    table.drawOn(c, 30, y_tabla - (len(table_data) * 18))
    
    # Resumen Totales
    monto_ahorrado = sum([item['descuento'] for item in carrito])
    resumen_y = y_tabla - (len(table_data) * 18) - 30
    c.setFont("Calibri-Bold", 10)
    detalles = ["Monto sin IVA:", "IVA:", "Monto Total:","Monto ahorrado:"]
    valores = [f"C${subtotal:.2f}", f"C${iva:.2f}", f"C${total:.2f}",f"C${monto_ahorrado:.2f}"]

    for i, (d, v) in enumerate(zip(detalles, valores)):
        y = resumen_y - i * 15
        c.drawString(350, y, d)
        c.drawString(410, y, "")
        c.drawRightString(560, y, v)

    # Políticas
    politica = [
        "Los productos vendidos por Panda Store tienen garantía de 1 mes a partir de la fecha de compra.",
        "No cubre daños por mal uso o accidentes.",
        "Pago inmediato salvo acuerdo escrito.",
        "Métodos aceptados: transferencia bancaria y efectivo."
    ]
    c.setFont("Calibri", 7)
    y = resumen_y - 60
    for linea in politica:
        c.drawString(30, y, linea)
        y -= 10

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

    
st.set_page_config(page_title="Panda Facturación", layout="centered")
st.image("https://i.imgur.com/NZFZZvD.jpeg", width=150)
st.title("Facturación Digital - Panda App")

menu = st.sidebar.selectbox("Menú", ["Crear Factura", "Historial"])

proveedores_info = {
    'Panda Store': 'https://i.imgur.com/NZFZZvD.png',
    'Cargotrans': 'https://i.imgur.com/BdIHbRs.png',
    'PedidosYa': 'https://i.imgur.com/KxhxMwF.png'
}

if "carrito" not in st.session_state:
    st.session_state.carrito = []
    
if menu == "Crear Factura":
    st.subheader("📄 Crear Factura")
    uploaded_file = st.file_uploader("Sube tu archivo Excel de productos", type=["xlsx"])
    if uploaded_file:
        productos = leer_productos_excel(uploaded_file)
        nombre = st.text_input("Nombre del Cliente")
        celular = st.text_input("Celular")
        if not celular.isnumeric() and celular != "":
            st.warning("Por favor ingrese solo números en el campo Celular.")
            celular = ""
        direccion = st.text_input("Dirección")

        proveedor = st.selectbox("Selecciona el proveedor", list(proveedores_info.keys()))
        st.image(proveedores_info[proveedor], width=150)

        texto_buscar = st.text_input("Buscar producto")
        productos_filtrados = [p for p in productos if texto_buscar.lower() in p['descripcion'].lower()]

        carrito = st.session_state.carrito
        
        for p in productos_filtrados:
            with st.expander(p['descripcion']):
                st.image(p['imagen'], width=150)
                st.write(f"Precio: C${p['precio']:.2f}")
                cantidad = st.number_input(f"Cantidad - {p['descripcion']}", min_value=0, step=1, key=p['codigo'])
                descuento = st.number_input(f"Descuento (C$) - {p['descripcion']}", min_value=0.0, step=1.0, key=str(p['codigo'])+'_desc')
                if cantidad > 0:
                    subtotal = p['precio'] * cantidad
                    total_linea = subtotal - descuento
                    
                    nuevo_item = {
                        "descripcion": p['descripcion'],
                        "cantidad": cantidad,
                        "precio": p['precio'],
                        "subtotal": subtotal,
                        "descuento": descuento,
                        "total_linea": total_linea
                    }
                    
                    ya_existe = any(
                        isinstance(item, dict) and 'descripcion' in item and item['descripcion'] == nuevo_item['descripcion']
                        for item in carrito
                    )

                    if not ya_existe:
                        carrito.append(nuevo_item)
                    

        if carrito:
            st.subheader("Vista Previa de la Factura")
            st.image("https://i.imgur.com/NZFZZvD.jpeg", width=100)
            st.markdown(f"**Cliente:** {nombre}")
            st.markdown(f"**Celular:** {celular}")
            st.markdown(f"**Dirección:** {direccion}")
            st.markdown(f"**Proveedor:** {proveedor}")

            factura_df = pd.DataFrame(carrito)
            st.dataframe(factura_df[["cantidad", "descripcion", "precio", "subtotal", "descuento", "total_linea"]])

            st.subheader("🗑 Eliminar productos del carrito")
            
            for idx, item in enumerate(carrito):
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.markdown(f"**{item['descripcion']}** - Cantidad: {item['cantidad']} - Total: C${item['total_linea']:.2f}")
                with col2:
                    if st.button("❌", key=f"delete_{idx}"):
                        st.session_state.carrito.pop(idx)
                        st.rerun()
            
            
            subtotal_total = factura_df["total_linea"].sum() / 1.15
            iva_total = factura_df["total_linea"].sum() - subtotal_total
            total_total = factura_df["total_linea"].sum()

            st.success(f"Subtotal: C${subtotal_total:.2f} | IVA: C${iva_total:.2f} | Total: C${total_total:.2f}")

            if st.button("Confirmar y Generar Factura"):
                pdf = generar_pdf(nombre, celular, direccion, proveedor, carrito, total_total, subtotal_total, iva_total)
                incrementar_numero_factura()
                factura_data = {
                    "Factura": obtener_numero_factura()-1,
                    "Fecha": datetime.now().strftime('%Y-%m-%d %H:%M'),
                    "Cliente": nombre,
                    "Teléfono": celular,
                    "Dirección": direccion,
                    "Total": total_total
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
