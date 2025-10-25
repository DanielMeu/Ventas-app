import sqlite3
import streamlit as st
import pandas as pd
from datetime import date

# ------------------ CONFIG ------------------
# 👉 Cambiar a la ruta de tu Google Drive si querés sincronizar
DB_PATH = "ventas.db"  

def get_connection():
    return sqlite3.connect(DB_PATH)

st.set_page_config(page_title="Sistema de Ventas", layout="wide")

page_bg = """
<style>
    .stApp { background-color: #33B5FF; }
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)
st.title("📊 Sistema de Gestión de Ventas")

# ------------------ UTILS ------------------
def mostrar_tabla(nombre_tabla):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {nombre_tabla}", conn)
    conn.close()
    st.dataframe(df, width=True)
    return df

def ejecutar_sql(sql, params=()):
    conn = get_connection()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

# ------------------ CRUD CLIENTES ------------------
def crud_clientes():
    st.subheader("👤 Gestión de Clientes")
    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True)

    if op == "Ver":
        mostrar_tabla("Clientes")

    elif op == "Insertar":
        nombre = st.text_input("Nombre")
        domi = st.text_input("Domicilio")
        telef = st.text_input("Teléfono")
        obs = st.text_area("Observaciones")
        estado = st.selectbox("Estado", ["A", "I"], index=0)
        if st.button("Guardar Cliente"):
            ejecutar_sql(
                "INSERT INTO Clientes (Nomb_cliente, Domi_Cliente, Telef_Cliente, Obs_Cliente, Estado_Cliente) VALUES (?, ?, ?, ?, ?)",
                (nombre, domi, telef, obs, estado)
            )
            st.success("Cliente agregado ✅")

    elif op == "Editar":
        df = mostrar_tabla("Clientes")
        if not df.empty:
            ids = df["id_cliente"].tolist()
            id_sel = st.selectbox("Seleccione ID a editar:", ids)
            cliente = df[df["id_cliente"] == id_sel].iloc[0]

            nombre = st.text_input("Nombre", cliente["Nomb_cliente"])
            domi = st.text_input("Domicilio", cliente["Domi_Cliente"])
            telef = st.text_input("Teléfono", cliente["Telef_Cliente"])
            obs = st.text_area("Observaciones", cliente["Obs_Cliente"])
            estado = st.selectbox("Estado", ["A", "I"], index=0 if cliente["Estado_Cliente"] == "A" else 1)

            if st.button("Actualizar Cliente"):
                ejecutar_sql(
                    "UPDATE Clientes SET Nomb_cliente=?, Domi_Cliente=?, Telef_Cliente=?, Obs_Cliente=?, Estado_Cliente=? WHERE id_cliente=?",
                    (nombre, domi, telef, obs, estado, id_sel)
                )
                st.success("Cliente actualizado ✅")

    elif op == "Eliminar":
        id_cliente = st.number_input("ID Cliente", min_value=1, step=1)
        if st.button("Eliminar Cliente"):
            ejecutar_sql("DELETE FROM Clientes WHERE id_cliente=?", (id_cliente,))
            st.warning("Cliente eliminado 🗑")

# ------------------ CRUD PROVEEDORES ------------------
def crud_proveedores():
    st.subheader("🏢 Gestión de Proveedores")
    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True)

    if op == "Ver":
        mostrar_tabla("Proveedores")

    elif op == "Insertar":
        nombre = st.text_input("Nombre")
        domi = st.text_input("Domicilio")
        telef = st.text_input("Teléfono")
        obs = st.text_area("Observaciones")
        estado = st.selectbox("Estado", ["A", "I"], index=0)
        if st.button("Guardar Proveedor"):
            ejecutar_sql(
                "INSERT INTO Proveedores (Nomb_Prove, Domi_Prove, Telef_Prove, Obs_Prove, Estado_Prove) VALUES (?, ?, ?, ?, ?)",
                (nombre, domi, telef, obs, estado)
            )
            st.success("Proveedor agregado ✅")

    elif op == "Editar":
        df = mostrar_tabla("Proveedores")
        if not df.empty:
            ids = df["id_prove"].tolist()
            id_sel = st.selectbox("Seleccione ID a editar:", ids)
            prove = df[df["id_prove"] == id_sel].iloc[0]

            nombre = st.text_input("Nombre", prove["Nomb_Prove"])
            domi = st.text_input("Domicilio", prove["Domi_Prove"])
            telef = st.text_input("Teléfono", prove["Telef_Prove"])
            obs = st.text_area("Observaciones", prove["Obs_Prove"])
            estado = st.selectbox("Estado", ["A", "I"], index=0 if prove["Estado_Prove"] == "A" else 1)

            if st.button("Actualizar Proveedor"):
                ejecutar_sql(
                    "UPDATE Proveedores SET Nomb_Prove=?, Domi_Prove=?, Telef_Prove=?, Obs_Prove=?, Estado_Prove=? WHERE id_prove=?",
                    (nombre, domi, telef, obs, estado, id_sel)
                )
                st.success("Proveedor actualizado ✅")

    elif op == "Eliminar":
        id_prove = st.number_input("ID Proveedor", min_value=1, step=1)
        if st.button("Eliminar Proveedor"):
            ejecutar_sql("DELETE FROM Proveedores WHERE id_prove=?", (id_prove,))
            st.warning("Proveedor eliminado 🗑")

# ------------------ CRUD STOCK ------------------
def crud_stock():
    st.subheader("📦 Gestión de Stock")
    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True)

    if op == "Ver":
        mostrar_tabla("Stock")
       
    elif op == "Insertar":
        talle = st.text_input("Talle")
        descr = st.text_input("Descripción")
        cant = st.number_input("Cantidad", min_value=0, step=1)
        pcio_vta = st.number_input("Precio Venta", min_value=0.0, step=0.1)
        pcio_costo = st.number_input("Precio Costo", min_value=0.0, step=0.1)
        id_prov = st.number_input("ID Proveedor", min_value=0, step=1)
        obs = st.text_area("Observaciones")
        estado = st.selectbox("Estado", ["A", "I"], index=0)

        if st.button("Guardar Producto"):
            ejecutar_sql(
                "INSERT INTO Stock (Talle_Stock, Descrip_Stock, Cant_Stock, Pcio_Vta_Stock, Pcio_Costo_Stock, id_proveedor, Obs_Stock, Estado_Stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (talle, descr, cant, pcio_vta, pcio_costo, id_prov, obs, estado)
            )
            st.success("Producto agregado ✅")

    elif op == "Editar":
        df = mostrar_tabla("Stock")
        if not df.empty:
            ids = df["id_producto_Stock"].tolist()
            id_sel = st.selectbox("Seleccione ID a editar:", ids)
            prod = df[df["id_producto_Stock"] == id_sel].iloc[0]

            talle = st.text_input("Talle", prod["Talle_Stock"])
            descr = st.text_input("Descripción", prod["Descrip_Stock"])
            cant = st.number_input("Cantidad", value=int(prod["Cant_Stock"]), step=1)
            pcio_vta = st.number_input("Precio Venta", value=float(prod["Pcio_Vta_Stock"]), step=0.1)
            pcio_costo = st.number_input("Precio Costo", value=float(prod["Pcio_Costo_Stock"]), step=0.1)
            id_prov = st.number_input("ID Proveedor", value=int(prod["id_proveedor"]) if prod["id_proveedor"] else 0, step=1)
            obs = st.text_area("Observaciones", prod["Obs_Stock"])
            estado = st.selectbox("Estado", ["A", "I"], index=0 if prod["Estado_Stock"] == "A" else 1)

            if st.button("Actualizar Producto"):
                ejecutar_sql(
                    "UPDATE Stock SET Talle_Stock=?, Descrip_Stock=?, Cant_Stock=?, Pcio_Vta_Stock=?, Pcio_Costo_Stock=?, id_proveedor=?, Obs_Stock=?, Estado_Stock=? WHERE id_producto_Stock=?",
                    (talle, descr, cant, pcio_vta, pcio_costo, id_prov, obs, estado, id_sel)
                )
                st.success("Producto actualizado ✅")

    elif op == "Eliminar":
        id_prod = st.number_input("ID Producto", min_value=1, step=1)
        if st.button("Eliminar Producto"):
            ejecutar_sql("DELETE FROM Stock WHERE id_producto_Stock=?", (id_prod,))
            st.warning("Producto eliminado 🗑")

# ------------------ CRUD VENTAS ------------------
def crud_ventas():
    st.subheader("🧾 Gestión de Ventas")
    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True)

    if op == "Ver":
        mostrar_tabla("Ventas")

    elif op == "Insertar":
        fecha = st.date_input("Fecha", value=date.today())
        id_cliente = st.number_input("ID Cliente", min_value=1, step=1)
        total = st.number_input("Total Venta", min_value=0.0, step=0.1)

        if st.button("Guardar Venta"):
            ejecutar_sql(
                "INSERT INTO Ventas (Fecha_Vtas, id_cliente, Total_Vtas) VALUES (?, ?, ?)",
                (fecha, id_cliente, total)
            )
            st.success("Venta agregada ✅")

    elif op == "Editar":
        df = mostrar_tabla("Ventas")
        if not df.empty:
            ids = df["id_Venta_Vtas"].tolist()
            id_sel = st.selectbox("Seleccione ID a editar:", ids)
            vta = df[df["id_Venta_Vtas"] == id_sel].iloc[0]

            fecha = st.date_input("Fecha", pd.to_datetime(vta["Fecha_Vtas"]).date())
            id_cliente = st.number_input("ID Cliente", value=int(vta["id_cliente"]) if vta["id_cliente"] else 0, step=1)
            total = st.number_input("Total Venta", value=float(vta["Total_Vtas"]), step=0.1)

            if st.button("Actualizar Venta"):
                ejecutar_sql(
                    "UPDATE Ventas SET Fecha_Vtas=?, id_cliente=?, Total_Vtas=? WHERE id_Venta_Vtas=?",
                    (fecha, id_cliente, total, id_sel)
                )
                st.success("Venta actualizada ✅")

    elif op == "Eliminar":
        id_venta = st.number_input("ID Venta", min_value=1, step=1)
        if st.button("Eliminar Venta"):
            ejecutar_sql("DELETE FROM Ventas WHERE id_Venta_Vtas=?", (id_venta,))
            st.warning("Venta eliminada 🗑")

# ------------------ CRUD DETALLEVENTAS ------------------
def crud_detalleventas():
    st.subheader("📑 Gestión de Detalle de Ventas")
    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True)

    if op == "Ver":
        mostrar_tabla("DetalleVentas")

    elif op == "Insertar":
        id_venta = st.number_input("ID Venta", min_value=1, step=1)
        fecha = st.date_input("Fecha", value=date.today())
        id_cliente = st.number_input("ID Cliente", min_value=1, step=1)
        id_prod = st.number_input("ID Producto", min_value=1, step=1)
        talle = st.text_input("Talle")
        cant = st.number_input("Cantidad", min_value=1, step=1)
        pcio_unit = st.number_input("Precio Unitario", min_value=0.0, step=0.1)
        pcio_total = cant * pcio_unit
        pcio_costo = st.number_input("Costo Unitario", min_value=0.0, step=0.1)
        obs = st.text_area("Observaciones")
        estado = st.selectbox("Estado", ["A", "I"], index=0)

        if st.button("Guardar Detalle"):
            ejecutar_sql(
                "INSERT INTO DetalleVentas (id_venta_Vtas, Fecha_DVtas, id_Cliente, id_producto_Stock, Talle_DVtas, Cant_DVtas, Pcio_Unitario_DVtas, Pcio_Total_DVtas, Pcio_Costo_Unit_DVtas, Obs_DVtas, Estado_DVtas) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (id_venta, fecha, id_cliente, id_prod, talle, cant, pcio_unit, pcio_total, pcio_costo, obs, estado)
            )
            st.success("Detalle de venta agregado ✅")

    elif op == "Editar":
        df = mostrar_tabla("DetalleVentas")
        if not df.empty:
            ids = df["id_detalle_DVtas"].tolist()
            id_sel = st.selectbox("Seleccione ID a editar:", ids)
            det = df[df["id_detalle_DVtas"] == id_sel].iloc[0]

            id_venta = st.number_input("ID Venta", value=int(det["id_venta_Vtas"]), step=1)
            fecha = st.date_input("Fecha", pd.to_datetime(det["Fecha_DVtas"]).date())
            id_cliente = st.number_input("ID Cliente", value=int(det["id_Cliente"]), step=1)
            id_prod = st.number_input("ID Producto", value=int(det["id_producto_Stock"]), step=1)
            talle = st.text_input("Talle", det["Talle_DVtas"])
            cant = st.number_input("Cantidad", value=int(det["Cant_DVtas"]), step=1)
            pcio_unit = st.number_input("Precio Unitario", value=float(det["Pcio_Unitario_DVtas"]), step=0.1)
            pcio_total = cant * pcio_unit
            pcio_costo = st.number_input("Costo Unitario", value=float(det["Pcio_Costo_Unit_DVtas"]), step=0.1)
            obs = st.text_area("Observaciones", det["Obs_DVtas"])
            estado = st.selectbox("Estado", ["A", "I"], index=0 if det["Estado_DVtas"] == "A" else 1)

            if st.button("Actualizar Detalle"):
                ejecutar_sql(
                    "UPDATE DetalleVentas SET id_venta_Vtas=?, Fecha_DVtas=?, id_Cliente=?, id_producto_Stock=?, Talle_DVtas=?, Cant_DVtas=?, Pcio_Unitario_DVtas=?, Pcio_Total_DVtas=?, Pcio_Costo_Unit_DVtas=?, Obs_DVtas=?, Estado_DVtas=? WHERE id_detalle_DVtas=?",
                    (id_venta, fecha, id_cliente, id_prod, talle, cant, pcio_unit, pcio_total, pcio_costo, obs, estado, id_sel)
                )
                st.success("Detalle actualizado ✅")

    elif op == "Eliminar":
        id_det = st.number_input("ID Detalle Venta", min_value=1, step=1)
        if st.button("Eliminar Detalle"):
            ejecutar_sql("DELETE FROM DetalleVentas WHERE id_detalle_DVtas=?", (id_det,))
            st.warning("Detalle eliminado 🗑")

# ------------------ MENÚ ------------------
menu = st.sidebar.selectbox(
    "Menú Principal",
    ["Clientes", "Proveedores", "Stock", "Ventas", "DetalleVentas"]
)

if menu == "Clientes":
    crud_clientes()
elif menu == "Proveedores":
    crud_proveedores()
elif menu == "Stock":
    crud_stock()
elif menu == "Ventas":
    crud_ventas()
elif menu == "DetalleVentas":
    crud_detalleventas()
