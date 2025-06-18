import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

DATA_FILE = "inventario.json"
st.set_page_config(page_title="Inventario La Villa", layout="wide")

# Cargar los datos desde el archivo JSON
def cargar_datos():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=["PRODUCTO","PROVEEDOR","ACTIVO","CATEGORIA","UNM","LOTE","CADUCIDAD","STOCK"])
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

# Guardar los datos en el archivo JSON
def guardar_datos(df):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(df.to_dict(orient="records"), f, indent=4, ensure_ascii=False)

# Función para iniciar sesión
def login():
    with st.sidebar:
        st.subheader("🔒 Administrador")
        usuario = st.text_input("Usuario")
        clave = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if usuario == "YHUERTA" and clave == "183":
                st.session_state["admin"] = True  # Marcar al usuario como administrador
                st.success("Acceso concedido")
            else:
                st.error("Credenciales incorrectas")

# Función para comprobar si un producto está caducado
def esta_caducado(fecha_str):
    try:
        fecha = pd.to_datetime(fecha_str, errors="coerce").date()  # Convertir a tipo de dato fecha
        return fecha < date.today()  # Comparar si es menor que la fecha actual
    except:
        return False

# Vista de inventario para el usuario normal
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
            return ['color: red'] * len(row)  # Resaltar la fila si está caducada
        else:
            return [''] * len(row)

    st.dataframe(df.style.apply(destacar_fila, axis=1), use_container_width=True)

# Vista de administración de productos para el administrador
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

            # Cambiar el formato del campo de fecha
            caducidad_default = datetime.today().date()
            nuevo["CADUCIDAD"] = st.date_input("Caducidad", value=caducidad_default)

            nuevo["STOCK"] = st.number_input("Stock", min_value=0, step=1)

            submitted = st.form_submit_button("Agregar")
            if submitted:
                if not nuevo["PRODUCTO"]:
                    st.error("El campo Producto es obligatorio.")
                else:
                    df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
                    guardar_datos(df)
                    st.success("Producto agregado correctamente.")
                    # Eliminar st.experimental_rerun() para evitar el error
                    return  # No se hace un rerun, pero se puede actualizar los datos sin reiniciar

    st.markdown("### ✏️ Editar / ❌ Eliminar productos existentes")

    for i, row in df.iterrows():
        with st.expander(row['PRODUCTO']):
            lote = st.text_input("Lote", value=row["LOTE"], key=f"lote_{i}")
            stock = st.number_input("Stock", value=int(row["STOCK"]), key=f"stock_{i}")
            
            # Mostrar y editar la fecha de caducidad con formato DD/MM/YYYY
            caducidad_fecha = pd.to_datetime(row["CADUCIDAD"], errors="coerce").date()
            caducidad = st.date_input("Caducidad", value=caducidad_fecha, key=f"caducidad_{i}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Guardar cambios", key=f"guardar_{i}"):
                    df.at[i, "LOTE"] = lote
                    df.at[i, "STOCK"] = stock
                    df.at[i, "CADUCIDAD"] = caducidad.strftime("%Y-%m-%d")
                    guardar_datos(df)
                    st.success("Cambios guardados.")
                    return  # Evitar el uso de st.experimental_rerun()

            with col2:
                if st.button("Eliminar producto", key=f"eliminar_{i}"):
                    df = df.drop(i).reset_index(drop=True)
                    guardar_datos(df)
                    st.warning("Producto eliminado.")
                    return  # Evitar el uso de st.experimental_rerun()

# Revisión y manejo de estado de sesión
if "admin" not in st.session_state:
    st.session_state["admin"] = False

# Verificar si el usuario está logueado o no
if not st.session_state["admin"]:
    login()  # Si no está logueado, mostrar el formulario de login

# Mostrar las vistas de acuerdo con el estado de sesión
if st.session_state["admin"]:
    df = cargar_datos()  # Cargar los datos solo si está logueado
    vista_admin(df)
else:
    df = cargar_datos()  # Cargar los datos para la vista de inventario
    vista_inventario(df)
