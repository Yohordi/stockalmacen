import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

DATA_FILE = "inventario.json"
st.set_page_config(page_title="Inventario La Villa", layout="wide")

def cargar_datos():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["PRODUCTO","PROVEEDOR","ACTIVO","CATEGORIA","UNM","LOTE","CADUCIDAD","STOCK"])
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

def guardar_datos(df):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4, ensure_ascii=False)

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

def esta_caducado(fecha_str):
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        return fecha < date.today()
    except:
        return False

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

def vista_admin(df):
    st.subheader("🛠️ Administración de Productos")

    with st.expander("➕ Agregar nuevo producto"):
        with st.form("form_nuevo"):
            nuevo = {}
            nuevo["PRODUCTO"] = st.text_input("Producto")
            nuevo["PROVEEDOR"] = st.text_input("Proveedor")
            nuevo["ACTIVO"] = st.text_input("Activo")
            nuevo["CATEGORIA"] = st.text_input("Categoría")
            nuevo["UNM"] = st.text_input("Unidad de medida")
            nuevo["LOTE"] = st.text_input("Lote")
            
            # Convertir y manejar la fecha de caducidad
            nuevo["CADUCIDAD"] = st.date_input("Caducidad").strftime("%Y-%m-%d")
            
            nuevo["STOCK"] = st.number_input("Stock", min_value=0, step=1)

            submitted = st.form_submit_button("Agregar")
            if submitted:
                if not nuevo["PRODUCTO"]:
                    st.error("El campo Producto es obligatorio.")
                else:
                    df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
                    guardar_datos(df)
                    st.success("Producto agregado correctamente.")
                    st.experimental_rerun()

    st.markdown("### ✏️ Editar / ❌ Eliminar productos existentes")

    for i, row in df.iterrows():
        with st.expander(row['PRODUCTO']):
            lote = st.text_input("Lote", value=row["LOTE"], key=f"lote_{i}")
            stock = st.number_input("Stock", value=int(row["STOCK"]), key=f"stock_{i}")
            
            # Convertir fecha y manejar errores
            try:
                caducidad_fecha = pd.to_datetime(row["CADUCIDAD"], errors="coerce").date()  # Usar pd.to_datetime para manejar diferentes formatos
                if pd.isna(caducidad_fecha):  # Si la conversión falla, asignamos la fecha actual
                    caducidad_fecha = datetime.today().date()
            except Exception as e:
                caducidad_fecha = datetime.today().date()  # Fallback en caso de error en la conversión

            caducidad = st.date_input("Caducidad", value=caducidad_fecha, key=f"caducidad_{i}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Guardar cambios", key=f"guardar_{i}"):
                    df.at[i, "LOTE"] = lote
                    df.at[i, "STOCK"] = stock
                    df.at[i, "CADUCIDAD"] = caducidad.strftime("%Y-%m-%d")
                    guardar_datos(df)
                    st.success("Cambios guardados.")
                    st.experimental_rerun()
            with col2:
                if st.button("Eliminar producto", key=f"eliminar_{i}"):
                    df = df.drop(i).reset_index(drop=True)
                    guardar_datos(df)
                    st.warning("Producto eliminado.")
                    st.experimental_rerun()

# Inicialización
if "admin" not in st.session_state:
    st.session_state["admin"] = False

df = cargar_datos()

# Mostrar vista según el estado de sesión
if st.session_state["admin"]:
    vista_admin(df)
else:
    vista_inventario(df)
