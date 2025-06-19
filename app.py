import streamlit as st
import pandas as pd
from datetime import datetime, date

# Ruta local del archivo Excel (ajustada a tu escritorio)
EXCEL_PATH = "C:/Users/USER/OneDrive/Desktop/almacen.xlsx"

st.set_page_config(page_title="Inventario La Villa", layout="wide")

# Leer los datos desde el Excel
def cargar_datos():
    df = pd.read_excel(EXCEL_PATH, sheet_name="CODIFICACION", usecols="A:J", header=None, skiprows=1)
    df.columns = ["CODIGO", "PRODUCTO", "PROVEEDOR", "ACTIVO", "CATEGORIA", "UNM", "?", "CADUCIDAD", "STOCK", "LOTE"]
    df = df[["PRODUCTO", "PROVEEDOR", "ACTIVO", "CATEGORIA", "UNM", "LOTE", "CADUCIDAD", "STOCK"]]
    return df

# Login del administrador
def login():
    with st.sidebar:
        st.subheader("🔒 Administrador")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if usuario == "YHUERTA" and clave == "183":
                st.session_state["admin"] = True
                st.success("Acceso concedido")
            else:
                st.error("Credenciales incorrectas")

# Verificación de productos caducados
def esta_caducado(fecha_str):
    try:
        fecha = pd.to_datetime(fecha_str, errors="coerce").date()
        return fecha < date.today()
    except:
        return False

# Vista para consulta
def vista_inventario(df):
    st.title("📦 Inventario General - Almacén La Villa")

    col1, col2 = st.columns(2)
    proveedor = col1.selectbox("Filtrar por proveedor", ["Todos"] + sorted(df["PROVEEDOR"].dropna().unique()))
    busqueda = col2.text_input("Buscar producto")

    if proveedor != "Todos":
        df = df[df["PROVEEDOR"] == proveedor]
    if busqueda:
        df = df[df["PRODUCTO"].str.contains(busqueda, case=False, na=False)]

    def destacar_fila(row):
        if row["STOCK"] == 0:
            return ['background-color: red; color: white'] * len(row)
        elif esta_caducado(row["CADUCIDAD"]):
            return ['color: red'] * len(row)
        else:
            return [''] * len(row)

    st.dataframe(df.style.apply(destacar_fila, axis=1), use_container_width=True)

# Vista para administrador (solo visual en esta versión)
def vista_admin(df):
    st.subheader("🛠️ Vista de administrador")
    st.markdown("Los datos se están leyendo directamente desde el archivo Excel.")
    st.dataframe(df, use_container_width=True)

# Control de sesión
if "admin" not in st.session_state:
    st.session_state["admin"] = False

if not st.session_state["admin"]:
    login()

df = cargar_datos()

if st.session_state["admin"]:
    vista_admin(df)
else:
    vista_inventario(df)

