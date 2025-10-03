import sqlite3
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from datetime import date
from io import StringIO
import os
import shutil
import datetime

# =====================
# CONFIGURACIÓN
# =====================
DB_PATH = "ventas.db"  # Cambiá a la ruta en tu Google Drive si sincronizás el archivo

st.set_page_config(page_title="Sistema de Ventas", layout="wide")
st.title("Sistema de Gestión de Ventas")

# =====================
# ESTILOS GLOBALES
# =====================
#                   Para cambiar color, tamaño, alineación o espaciado, se hace solo en el bloque <style> al inicio.
#                   Se pueden definir varias clases (.header-blue, .header-red, etc.) para jugar con estilos distintos.
st.markdown(
    """
    <style>
        .app-header {
            text-align: left;      /* alineación: left, center o right */
            font-size: 26px;         /* tamaño de letra */
            font-weight: 700;        /* 400=normal, 700=bold */
            color: #0a66c2;          /* color azul corporativo */
            margin-bottom: 20px;     /* espacio debajo del título */
        }
    </style>
    """,
    unsafe_allow_html=True
)


# Fondo opcional
st.markdown(
#    """
#    <style>
#        .stApp { background-color: #F5FBFF; }
#        .small-muted { color: #666; font-size: 0.85rem; }
#        .ok { color: #0a7; }
#        .warn { color: #c70; }
#        .err { color: #b00; }
#    </style>
#    """
    """
    <style>
        .stApp { background-color: #33B5FF; }
    </style>
    """
    ,
    unsafe_allow_html=True,
)

# Carpeta donde guardamos los backups
BACKUP_DIR = "backups"
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# =====================
# UTILIDADES DB
# =====================
@st.cache_resource(show_spinner=False)
def get_connection():
    # check_same_thread=False permite usar la conexión en hilos de Streamlit
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def run_query(sql: str, params: tuple | list = ()):  # INSERT/UPDATE/DELETE
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    return cur.lastrowid


def fetch_df(sql: str, params: tuple | list = ()):  # SELECT a DataFrame
    conn = get_connection()
    df = pd.read_sql_query(sql, conn, params=params)
    return df


# Helpers de listas (id -> nombre)
def df_to_select_options(df: pd.DataFrame, id_col: str, label_cols: list[str]):
    """Devuelve: labels(list), ids(list). label es concatenación de label_cols."""
    if df.empty:
        return ["<sin datos>"] , [None]
    labels = (
        df[label_cols]
        .astype(str)
        .agg(" - ".join, axis=1)
        .tolist()
    )
    ids = df[id_col].tolist()
    return labels, ids


# =====================
# VERIFICACIONES DE ESQUEMA (resumen y tolerancia a diferencias)
# =====================
# Nota: Tu SQL adjunto tiene pequeñas inconsistencias de nombres de FK. La app asume:
#   Proveedores.id_prove
#   Clientes.id_cliente
#   Stock.id_producto_Stock, Stock.id_proveedor (FK -> Proveedores.id_prove)
#   Colores_Stock: id_colores, id_producto_Stock, Color_colores, Cant_Stock_Colores
#   DetalleVentas SIN id_venta_Vtas y CON Color_DVtas
# Si tu tabla DetalleVentas aún tuviera id_venta_Vtas, mostrará un aviso en pantalla.


def table_exists(name: str) -> bool:
    df = fetch_df("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return not df.empty


def column_exists(table: str, col: str) -> bool:
    try:
        df = fetch_df(f"PRAGMA table_info({table})")
        return col in df['name'].values
    except Exception:
        return False

# ==========================
# FUNCIONES DE B_UP Y RESORE
# ==========================
def backup_db():
    """Genera una copia de seguridad de Ventas.db"""
    fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"Ventas_{fecha}.db")
    shutil.copy2("Ventas.db", backup_file)
    return backup_file

def restore_db(backup_file):
    """Restaura Ventas.db desde un backup"""
    if os.path.exists(backup_file):
        shutil.copy2(backup_file, "Ventas.db")
        return True
    return False

# ===============================
# FUNCIONES DE EDICION DE PRECIOS
# =============================== 

def format_currency(value):
    """Devuelve el valor en formato moneda con separador de miles y dos decimales."""
    try:
        return "${:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return "$0.00"


def format_dataframe(df, move_obs_stock=False):
    """Aplica formato moneda a las columnas de precios y opcionalmente mueve obs_stock al final."""
    currency_cols = [
        "Pcio_Vta_Stock",
        "Pcio_Costo_Stock",
        "Pcio_Unitario_DVtas",
        "Pcio_Total_DVtas",
        "Pcio_Costo_Unit_DVtas",
    ]

    for col in currency_cols:
        if col in df.columns:
            df[col] = df[col].apply(format_currency)

    # mover Obs_Stock al final (solo en pagina_lista_precios)
    if move_obs_stock and "Obs_Stock" in df.columns:
        cols = [c for c in df.columns if c != "Obs_Stock"] + ["Obs_Stock"]
        df = df[cols]

    return df



# =====================
# CRUD CLIENTES
# =====================

def crud_clientes():

    #st.text('Gestión de Clientes', width='content')
    
    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True, key="clientes_radio")

    if op == "Ver":
#        st.dataframe(fetch_df("SELECT * FROM Clientes"), use_container_width=True)  solo hasta 2025-12-31
        st.dataframe(fetch_df("SELECT * FROM Clientes"), width="stretch")       # para use_container_width=false  poner: ="content"


    elif op == "Insertar":
        c1, c2 = st.columns([2,2])
        with c1:
            nombre = st.text_input("Nombre")
            domi = st.text_input("Domicilio")
            telef = st.text_input("Teléfono")
        with c2:
            obs = st.text_area("Observaciones")
            estado = st.selectbox("Estado", ["A", "I"], index=0)
        if st.button("Guardar Cliente", type="primary"):
            run_query(
                """
                INSERT INTO Clientes (Nomb_cliente, Domi_Cliente, Telef_Cliente, Obs_Cliente, Estado_Cliente)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre, domi, telef, obs, estado),
            )
            st.success("Cliente agregado")

    elif op == "Editar":
        df = fetch_df("SELECT * FROM Clientes ORDER BY Nomb_cliente")
        labels, ids = df_to_select_options(df, "id_cliente", ["Nomb_cliente"]) if not df.empty else (["<sin clientes>"],[None])
        id_sel = st.selectbox("Cliente a editar", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin clientes>")
        if id_sel:
            cliente = df[df["id_cliente"] == id_sel].iloc[0]
            c1, c2 = st.columns([2,2])
            with c1:
                nombre = st.text_input("Nombre", cliente["Nomb_cliente"])
                domi = st.text_input("Domicilio", cliente["Domi_Cliente"])
                telef = st.text_input("Teléfono", cliente["Telef_Cliente"])
            with c2:
                obs = st.text_area("Observaciones", cliente["Obs_Cliente"])
                estado = st.selectbox("Estado", ["A", "I"], index=0 if cliente["Estado_Cliente"]=="A" else 1)
            if st.button("Actualizar Cliente", type="primary"):
                run_query(
                    """
                    UPDATE Clientes
                    SET Nomb_cliente=?, Domi_Cliente=?, Telef_Cliente=?, Obs_Cliente=?, Estado_Cliente=?
                    WHERE id_cliente=?
                    """,
                    (nombre, domi, telef, obs, estado, id_sel),
                )
                st.success("Cliente actualizado")

    elif op == "Eliminar":
        df = fetch_df("SELECT id_cliente, Nomb_cliente FROM Clientes ORDER BY Nomb_cliente")
        labels, ids = df_to_select_options(df, "id_cliente", ["Nomb_cliente"]) if not df.empty else (["<sin clientes>"],[None])
        id_sel = st.selectbox("Cliente a eliminar", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin clientes>")
        if id_sel and st.button("Eliminar Cliente", type="secondary"):
            run_query("DELETE FROM Clientes WHERE id_cliente=?", (id_sel,))
            st.warning("Cliente eliminado")


# =====================
# CRUD PROVEEDORES
# =====================

def crud_proveedores():

    #st.text('Gestión de Proveedores', width='content')

    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True, key="proveedores_radio")

    if op == "Ver":
        st.dataframe(fetch_df("SELECT * FROM Proveedores"), width="stretch")

    elif op == "Insertar":
        c1, c2 = st.columns([2,2])
        with c1:
            nombre = st.text_input("Nombre")
            domi = st.text_input("Domicilio")
            telef = st.text_input("Teléfono")
        with c2:
            obs = st.text_area("Observaciones")
            estado = st.selectbox("Estado", ["A", "I"], index=0)
        if st.button("Guardar Proveedor", type="primary"):
            run_query(
                """
                INSERT INTO Proveedores (Nomb_Prove, Domi_Prove, Telef_Prove, Obs_Prove, Estado_Prove)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nombre, domi, telef, obs, estado),
            )
            st.success("Proveedor agregado")

    elif op == "Editar":
        df = fetch_df("SELECT * FROM Proveedores ORDER BY Nomb_Prove")
        labels, ids = df_to_select_options(df, "id_prove", ["Nomb_Prove"]) if not df.empty else (["<sin proveedores>"],[None])
        id_sel = st.selectbox("Proveedor a editar", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin proveedores>")
        if id_sel:
            row = df[df["id_prove"] == id_sel].iloc[0]
            c1, c2 = st.columns([2,2])
            with c1:
                nombre = st.text_input("Nombre", row["Nomb_Prove"])
                domi = st.text_input("Domicilio", row["Domi_Prove"])
                telef = st.text_input("Teléfono", row["Telef_Prove"])
            with c2:
                obs = st.text_area("Observaciones", row["Obs_Prove"])
                estado = st.selectbox("Estado", ["A", "I"], index=0 if row["Estado_Prove"]=="A" else 1)
            if st.button("Actualizar Proveedor", type="primary"):
                run_query(
                    """
                    UPDATE Proveedores
                    SET Nomb_Prove=?, Domi_Prove=?, Telef_Prove=?, Obs_Prove=?, Estado_Prove=?
                    WHERE id_prove=?
                    """,
                    (nombre, domi, telef, obs, estado, id_sel),
                )
                st.success("Proveedor actualizado")

    elif op == "Eliminar":
        df = fetch_df("SELECT id_prove, Nomb_Prove FROM Proveedores ORDER BY Nomb_Prove")
        labels, ids = df_to_select_options(df, "id_prove", ["Nomb_Prove"]) if not df.empty else (["<sin proveedores>"],[None])
        id_sel = st.selectbox("Proveedor a eliminar", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin proveedores>")
        if id_sel and st.button("Eliminar Proveedor", type="secondary"):
            run_query("DELETE FROM Proveedores WHERE id_prove=?", (id_sel,))
            st.warning("Proveedor eliminado")


# =====================
# CRUD STOCK (Productos) + COLORES
# =====================

def view_stock_with_colors():

    sql = """
        SELECT s.id_producto_Stock, s.Descrip_Stock, s.Talle_Stock,
               s.Pcio_Vta_Stock, s.Pcio_Costo_Stock,
               p.Nomb_Prove AS Proveedor,
               c.Color_colores AS Color,
               c.Cant_Stock_Colores AS Cantidad
        FROM Stock s
        LEFT JOIN Proveedores p ON p.id_prove = s.id_proveedor
        LEFT JOIN Colores_Stock c ON c.id_producto_Stock = s.id_producto_Stock
        ORDER BY s.Descrip_Stock COLLATE NOCASE, c.Color_colores COLLATE NOCASE
    """

    df = fetch_df(sql)
    df = format_dataframe(df)
    st.dataframe(df, width="stretch")

    #st.dataframe(fetch_df(sql), width="stretch")


def crud_stock():

    #st.markdown("## Gestión de Stock")
    #st.text('Gestión de Stock', width='content')

    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar", "Colores de un producto"], horizontal=True, key="stock_radio")

    if op == "Ver":
        view_stock_with_colors()

    elif op == "Insertar":
        # Datos de proveedor para selectbox
        df_prov = fetch_df("SELECT id_prove, Nomb_Prove FROM Proveedores ORDER BY Nomb_Prove")
        prov_labels, prov_ids = df_to_select_options(df_prov, "id_prove", ["Nomb_Prove"]) if not df_prov.empty else (["<sin proveedores>"],[None])

        c1, c2, c3 = st.columns([2,2,2])
        with c1:
            talle = st.text_input("Talle")
            descr = st.text_input("Descripción")
            obs = st.text_area("Observaciones")
        with c2:
            pcio_vta = st.number_input("Precio Venta", min_value=0.0, step=0.1)
            pcio_costo = st.number_input("Precio Costo", min_value=0.0, step=0.1)
            estado = st.selectbox("Estado", ["A", "I"], index=0)
        with c3:
            id_prov_sel = st.selectbox("Proveedor", options=prov_ids, format_func=lambda x: prov_labels[prov_ids.index(x)] if x in prov_ids else "<sin proveedores>")
            # Color inicial opcional
            st.markdown("**Color inicial (opcional)**")
            color_ini = st.text_input("Color")
            cant_ini = st.number_input("Stock inicial", min_value=0, step=1)

        if st.button("Guardar Producto", type="primary"):
            new_id = run_query(
                """
                INSERT INTO Stock (Talle_Stock, Descrip_Stock, Pcio_Vta_Stock, Pcio_Costo_Stock, id_proveedor, Obs_Stock, Estado_Stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (talle, descr, pcio_vta, pcio_costo, id_prov_sel, obs, estado),
            )
            # Color inicial si se cargó
            if color_ini:
                color_mayus = color_ini.strip().upper()   # 🔹 ahora siempre en MAYUSCULAS
                run_query(
                    """
                    INSERT INTO Colores_Stock (id_producto_Stock, Color_colores, Cant_Stock_Colores)
                    VALUES (?, ?, ?)
                    """,
                    (new_id, color_mayus, int(cant_ini or 0)),
                )
            st.success(f"Producto agregado (ID {new_id})")

    elif op == "Editar":
        df_prod = fetch_df("SELECT * FROM Stock ORDER BY Descrip_Stock")
        labels, ids = df_to_select_options(df_prod, "id_producto_Stock", ["Descrip_Stock", "Talle_Stock"]) if not df_prod.empty else (["<sin productos>"],[None])
        id_sel = st.selectbox("Producto a editar", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin productos>")
        if id_sel:
            prod = df_prod[df_prod["id_producto_Stock"] == id_sel].iloc[0]
            df_prov = fetch_df("SELECT id_prove, Nomb_Prove FROM Proveedores ORDER BY Nomb_Prove")
            prov_labels, prov_ids = df_to_select_options(df_prov, "id_prove", ["Nomb_Prove"]) if not df_prov.empty else (["<sin proveedores>"],[None])

            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                talle = st.text_input("Talle", prod["Talle_Stock"])
                descr = st.text_input("Descripción", prod["Descrip_Stock"])
                obs = st.text_area("Observaciones", prod.get("Obs_Stock", ""))
            with c2:
                pcio_vta = st.number_input("Precio Venta", value=float(prod["Pcio_Vta_Stock"]), step=0.1)
                pcio_costo = st.number_input("Precio Costo", value=float(prod["Pcio_Costo_Stock"]), step=0.1)
                estado = st.selectbox("Estado", ["A", "I"], index=0 if prod.get("Estado_Stock", "A") == "A" else 1)
            with c3:
                prov_value = int(prod["id_proveedor"]) if pd.notnull(prod.get("id_proveedor")) else None
                id_prov_sel = st.selectbox("Proveedor", options=prov_ids, index=(prov_ids.index(prov_value) if prov_value in prov_ids else 0), format_func=lambda x: prov_labels[prov_ids.index(x)] if x in prov_ids else "<sin proveedores>")

            if st.button("Actualizar Producto", type="primary"):
                run_query(
                    """
                    UPDATE Stock
                    SET Talle_Stock=?, Descrip_Stock=?, Pcio_Vta_Stock=?, Pcio_Costo_Stock=?, id_proveedor=?, Obs_Stock=?, Estado_Stock=?
                    WHERE id_producto_Stock=?
                    """,
                    (talle, descr, pcio_vta, pcio_costo, id_prov_sel, obs, estado, id_sel),
                )
                st.success("Producto actualizado")

    elif op == "Eliminar":
        df_prod = fetch_df("SELECT id_producto_Stock, Descrip_Stock, Talle_Stock FROM Stock ORDER BY Descrip_Stock")
        labels, ids = df_to_select_options(df_prod, "id_producto_Stock", ["Descrip_Stock", "Talle_Stock"]) if not df_prod.empty else (["<sin productos>"],[None])
        id_sel = st.selectbox("Producto a eliminar", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin productos>")
        if id_sel and st.button("Eliminar Producto", type="secondary"):
            # Eliminamos colores primero (por si no hay ON DELETE CASCADE)
            run_query("DELETE FROM Colores_Stock WHERE id_producto_Stock=?", (id_sel,))
            run_query("DELETE FROM Stock WHERE id_producto_Stock=?", (id_sel,))
            st.warning("Producto eliminado (y sus colores)")

    elif op == "Colores de un producto":
        # Gestión específica del stock por color
        df_prod = fetch_df("SELECT id_producto_Stock, Descrip_Stock, Talle_Stock FROM Stock ORDER BY Descrip_Stock")
        labels, ids = df_to_select_options(df_prod, "id_producto_Stock", ["Descrip_Stock", "Talle_Stock"]) if not df_prod.empty else (["<sin productos>"],[None])
        id_sel = st.selectbox("Producto", options=ids, format_func=lambda x: labels[ids.index(x)] if x in ids else "<sin productos>")
        if id_sel:
            st.markdown("**Colores existentes**")
            df_col = fetch_df(
                "SELECT id_colores, Color_colores, Cant_Stock_Colores FROM Colores_Stock WHERE id_producto_Stock=? ORDER BY Color_colores",
                (id_sel,),
            )
            if df_col.empty:
                st.info("Este producto no tiene colores aún")
            # Editor por filas
            for i, row in df_col.iterrows():
                c1, c2, c3 = st.columns([3,2,1])
                with c1:
                    # 🔹 Ahora el campo color es editable y se  muestra siempre en mayúsculas
                    new_color = st.text_input(
                        "Color",
                        value=str(row["Color_colores"]).strip().upper(),
                        key=f"color_{row['id_colores']}"
                        #disabled=True
                    )
                with c2:
                    new_cant = st.number_input(
                        "Cantidad",
                        min_value=0,
                        step=1,
                        value=int(row["Cant_Stock_Colores"]),
                        key=f"cant_{row['id_colores']}"
                    )
                with c3:
                    if st.button("Actualizar", key=f"upd_{row['id_colores']}"):
                        run_query(
                            "UPDATE Colores_Stock SET Color_colores=?, Cant_Stock_Colores=? WHERE id_colores=?",
                            (new_color.strip().upper(), new_cant, int(row["id_colores"]))
                        )
                        st.success(f"Actualizado {str(row['Color_colores']).strip().upper()}")
            st.divider()
            st.markdown("**Agregar nuevo color**")
            col_new = st.text_input("Color nuevo")
            cant_new = st.number_input("Stock", min_value=0, step=1)
            if st.button("Agregar color", type="primary"):
                # 🔹 Guardar siempre en mayúsculas
                color_mayus = col_new.strip().upper()
                run_query(
                    "INSERT INTO Colores_Stock (id_producto_Stock, Color_colores, Cant_Stock_Colores) VALUES (?, ?, ?)",
                    (id_sel, color_mayus, int(cant_new or 0))
                )
                st.success(f"Color '{color_mayus}' agregado")

# =====================
# CRUD DETALLEVENTAS (sin cabecera Ventas)
# =====================

def crud_detalleventas():

    # Aviso si aún existe la columna id_venta_Vtas
    if column_exists("DetalleVentas", "id_venta_Vtas"):
        st.markdown(
            """
            <div class='warn'>Aviso: tu tabla <b>DetalleVentas</b> aún tiene la columna <b>id_venta_Vtas</b>.
            Esta app la ignora, pero te conviene eliminarla del esquema y agregar <b>Color_DVtas</b> (TEXT).</div>
            """,
            unsafe_allow_html=True,
        )

    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True, key="detalleventas_radio")

    if op == "Ver":
        # Vista enriquecida
        base_cols = [
            "d.id_detalle_DVtas", "d.Fecha_DVtas", "cli.Nomb_cliente AS Cliente",
            "s.Descrip_Stock AS Producto", "s.Talle_Stock AS TalleProducto",
            "d.Talle_DVtas AS TalleVenta", "d.Color_DVtas AS Color",
            "d.Cant_DVtas", "d.Pcio_Unitario_DVtas", "d.Pcio_Total_DVtas",
            "d.Pcio_Costo_Unit_DVtas", "d.Obs_DVtas", "d.Estado_DVtas"
        ]
        sql = f"""
            SELECT {', '.join(base_cols)}
            FROM DetalleVentas d
            LEFT JOIN Clientes cli ON cli.id_cliente = d.id_Cliente
            LEFT JOIN Stock s ON s.id_producto_Stock = d.id_producto_Stock
            ORDER BY d.Fecha_DVtas DESC, d.id_detalle_DVtas DESC
        """
        st.dataframe(fetch_df(sql), width="stretch")

    else:
        # Datos para selects
        df_cli = fetch_df("SELECT id_cliente, Nomb_cliente FROM Clientes ORDER BY Nomb_cliente")
        cli_labels, cli_ids = df_to_select_options(df_cli, "id_cliente", ["Nomb_cliente"]) if not df_cli.empty else (["<sin clientes>"],[None])

        df_prod = fetch_df("SELECT id_producto_Stock, Descrip_Stock, Talle_Stock, Pcio_Vta_Stock, Pcio_Costo_Stock FROM Stock ORDER BY Descrip_Stock")
        prod_labels, prod_ids = df_to_select_options(df_prod, "id_producto_Stock", ["Descrip_Stock", "Talle_Stock"]) if not df_prod.empty else (["<sin productos>"],[None])

        def color_options(product_id: int):
            d = fetch_df("SELECT Color_colores FROM Colores_Stock WHERE id_producto_Stock=? ORDER BY Color_colores", (product_id,))
            if d.empty:
                return ["<sin colores>"]
            return d["Color_colores"].astype(str).tolist()

        # ====================================================
        # INSERTAR
        # ====================================================
        if op == "Insertar":
            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                fecha = st.date_input("Fecha", value=date.today())
                id_cli = st.selectbox("Cliente", options=cli_ids, format_func=lambda x: cli_labels[cli_ids.index(x)] if x in cli_ids else "<sin clientes>")
            with c2:
                id_prod = st.selectbox("Producto", options=prod_ids, format_func=lambda x: prod_labels[prod_ids.index(x)] if x in prod_ids else "<sin productos>")
                talle_vta = st.text_input("Talle (venta) — opcional")
            with c3:
                colors = color_options(id_prod) if id_prod else ["<sin colores>"]
                color_sel = st.selectbox("Color", options=colors)

            # Defaults de precios
            pcio_unit_default = 0.0
            pcio_costo_default = 0.0
            if id_prod:
                rowp = df_prod[df_prod["id_producto_Stock"] == id_prod].iloc[0]
                pcio_unit_default = float(rowp["Pcio_Vta_Stock"]) or 0.0
                pcio_costo_default = float(rowp["Pcio_Costo_Stock"]) or 0.0

            c4, c5, c6 = st.columns([2,2,2])
            with c4:
                cant = st.number_input("Cantidad", min_value=1, step=1, value=1)
            with c5:
                pcio_unit = st.number_input("Precio Unitario", min_value=0.0, step=0.1, value=pcio_unit_default)
            with c6:
                pcio_costo = st.number_input("Costo Unitario", min_value=0.0, step=0.1, value=pcio_costo_default)

            pcio_total = cant * pcio_unit
            st.info(f"Total: {pcio_total:.2f}")
            obs = st.text_area("Observaciones")
            estado = st.selectbox("Estado", ["A", "I"], index=0)

            if st.button("Guardar Detalle", type="primary"):
                # ✅ Normalizar color
                color_norm = (color_sel or "").strip()

                # ✅ Verificar stock antes de insertar
                stock_ok = True
                if id_prod and color_norm and color_norm != "<sin colores>":
                    df_stock = fetch_df(
                        "SELECT Cant_Stock_Colores FROM Colores_Stock WHERE id_producto_Stock=? AND TRIM(UPPER(Color_colores))=TRIM(UPPER(?))",
                        (id_prod, color_norm)
                    )
                    if df_stock.empty:
                        st.error("❌ No se encontró stock para este producto/color.")
                        stock_ok = False
                    else:
                        stock_actual = int(df_stock.iloc[0]["Cant_Stock_Colores"])
                        if stock_actual <= 0:
                            st.warning(f"⚠️ El producto no tiene stock disponible para el color '{color_norm}'.")
                            stock_ok = False
                        elif cant > stock_actual:
                            st.warning(f"⚠️ Stock insuficiente. Disponible: {stock_actual}, solicitado: {cant}.")
                            stock_ok = False

                if stock_ok:
                    fecha_str = fecha.isoformat()
                    cols = [
                        "Fecha_DVtas", "id_Cliente", "id_producto_Stock", "Color_DVtas",
                        "Talle_DVtas", "Cant_DVtas", "Pcio_Unitario_DVtas", "Pcio_Total_DVtas",
                        "Pcio_Costo_Unit_DVtas", "Obs_DVtas", "Estado_DVtas"
                    ]
                    qmarks = ",".join(["?"] * len(cols))
                    run_query(
                        f"INSERT INTO DetalleVentas ({','.join(cols)}) VALUES ({qmarks})",
                        (fecha_str, id_cli, id_prod, color_norm, talle_vta, int(cant), float(pcio_unit),
                         float(pcio_total), float(pcio_costo), obs, estado),
                    )

                    # Descontar stock
                    if id_prod and color_norm and color_norm != "<sin colores>":
                        run_query(
                            """
                            UPDATE Colores_Stock
                            SET Cant_Stock_Colores = Cant_Stock_Colores - ?
                            WHERE id_producto_Stock=? AND TRIM(UPPER(Color_colores))=TRIM(UPPER(?))
                            """,
                            (int(cant), id_prod, color_norm),
                        )
                    st.success("✅ Detalle de venta agregado. Stock actualizado.")

        # ====================================================
        # EDITAR
        # ====================================================
        elif op == "Editar":
            df = fetch_df("SELECT * FROM DetalleVentas ORDER BY id_detalle_DVtas DESC")
            if df.empty:
                st.info("No hay detalles para editar")
                return
            ids = df["id_detalle_DVtas"].tolist()
            id_sel = st.selectbox("Detalle a editar (ID)", options=ids)
            det = df[df["id_detalle_DVtas"] == id_sel].iloc[0]

            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                fecha_val = pd.to_datetime(det["Fecha_DVtas"]).date()
                fecha = st.date_input("Fecha", value=fecha_val)
                id_cli = st.selectbox("Cliente", options=cli_ids, index=(cli_ids.index(det["id_Cliente"]) if det["id_Cliente"] in cli_ids else 0), format_func=lambda x: cli_labels[cli_ids.index(x)] if x in cli_ids else "<sin clientes>")
            with c2:
                id_prod = st.selectbox("Producto", options=prod_ids, index=(prod_ids.index(det["id_producto_Stock"]) if det["id_producto_Stock"] in prod_ids else 0), format_func=lambda x: prod_labels[prod_ids.index(x)] if x in prod_ids else "<sin productos>")
                talle_vta = st.text_input("Talle (venta)", det.get("Talle_DVtas", ""))
            with c3:
                colors = color_options(id_prod) if id_prod else ["<sin colores>"]
                current_color = (det.get("Color_DVtas", "") or "").strip()
                idx_color = colors.index(current_color) if current_color in colors else 0
                color_sel = st.selectbox("Color", options=colors, index=idx_color)

            c4, c5, c6 = st.columns([2,2,2])
            with c4:
                cant = st.number_input("Cantidad", min_value=1, step=1, value=int(det["Cant_DVtas"]))
            with c5:
                pcio_unit = st.number_input("Precio Unitario", min_value=0.0, step=0.1, value=float(det["Pcio_Unitario_DVtas"]))
            with c6:
                pcio_costo = st.number_input("Costo Unitario", min_value=0.0, step=0.1, value=float(det["Pcio_Costo_Unit_DVtas"]))

            pcio_total = cant * pcio_unit
            st.info(f"Total: {pcio_total:.2f}")
            obs = st.text_area("Observaciones", det.get("Obs_DVtas", ""))
            estado = st.selectbox("Estado", ["A", "I"], index=0 if det.get("Estado_DVtas", "A") == "A" else 1)

            if st.button("Actualizar Detalle", type="primary"):
                # ✅ Normalizar color
                color_norm = (color_sel or "").strip()

                # ✅ Verificar stock antes de actualizar
                stock_ok = True
                diferencia = cant - int(det["Cant_DVtas"])
                if id_prod and color_norm and color_norm != "<sin colores>" and diferencia != 0:
                    df_stock = fetch_df(
                        "SELECT Cant_Stock_Colores FROM Colores_Stock WHERE id_producto_Stock=? AND TRIM(UPPER(Color_colores))=TRIM(UPPER(?))",
                        (id_prod, color_norm)
                    )
                    if df_stock.empty:
                        st.error("❌ No se encontró stock para este producto/color.")
                        stock_ok = False
                    else:
                        stock_actual = int(df_stock.iloc[0]["Cant_Stock_Colores"])
                        if diferencia > 0 and stock_actual < diferencia:
                            st.warning(f"⚠️ Stock insuficiente. Disponible: {stock_actual}, necesitas {diferencia} adicionales.")
                            stock_ok = False

                if stock_ok:
                    fecha_str = fecha.isoformat()
                    run_query(
                        """
                        UPDATE DetalleVentas
                        SET Fecha_DVtas=?, id_Cliente=?, id_producto_Stock=?, Color_DVtas=?, Talle_DVtas=?,
                            Cant_DVtas=?, Pcio_Unitario_DVtas=?, Pcio_Total_DVtas=?, Pcio_Costo_Unit_DVtas=?,
                            Obs_DVtas=?, Estado_DVtas=?
                        WHERE id_detalle_DVtas=?
                        """,
                        (fecha_str, id_cli, id_prod, color_norm, talle_vta, int(cant), float(pcio_unit),
                         float(pcio_total), float(pcio_costo), obs, estado, id_sel),
                    )

                    # Ajustar stock si cambió la cantidad
                    if id_prod and color_norm and color_norm != "<sin colores>" and diferencia != 0:
                        run_query(
                            """
                            UPDATE Colores_Stock
                            SET Cant_Stock_Colores = Cant_Stock_Colores - ?
                            WHERE id_producto_Stock=? AND TRIM(UPPER(Color_colores))=TRIM(UPPER(?))
                            """,
                            (diferencia, id_prod, color_norm),
                        )
                    st.success("✅ Detalle actualizado y stock ajustado.")

        # ====================================================
        # ELIMINAR
        # ====================================================
        elif op == "Eliminar":
            df = fetch_df("SELECT * FROM DetalleVentas ORDER BY id_detalle_DVtas DESC")
            if df.empty:
                st.info("No hay registros para eliminar")

# =====================
# CRUD DETALLEVENTAS (sin cabecera Ventas)
# =====================

def crud_detalleventas():

    # Aviso si aún existe la columna id_venta_Vtas
    if column_exists("DetalleVentas", "id_venta_Vtas"):
        st.markdown(
            """
            <div class='warn'>Aviso: tu tabla <b>DetalleVentas</b> aún tiene la columna <b>id_venta_Vtas</b>.
            Esta app la ignora, pero te conviene eliminarla del esquema y agregar <b>Color_DVtas</b> (TEXT).</div>
            """,
            unsafe_allow_html=True,
        )

    # 🔹 Debug siempre visible
    debug_mode = st.checkbox("Mostrar debug", value=False)

    op = st.radio("Operación:", ["Ver", "Insertar", "Editar", "Eliminar"], horizontal=True, key="debug_radio")

    if op == "Ver":
        # Vista enriquecida
        base_cols = [
            "d.id_detalle_DVtas", "d.Fecha_DVtas", "cli.Nomb_cliente AS Cliente",
            "s.Descrip_Stock AS Producto", "s.Talle_Stock AS TalleProducto",
            "d.Talle_DVtas AS TalleVenta", "d.Color_DVtas AS Color",
            "d.Cant_DVtas", "d.Pcio_Unitario_DVtas", "d.Pcio_Total_DVtas",
            "d.Pcio_Costo_Unit_DVtas", "d.Obs_DVtas", "d.Estado_DVtas"
        ]
        sql = f"""
            SELECT {', '.join(base_cols)}
            FROM DetalleVentas d
            LEFT JOIN Clientes cli ON cli.id_cliente = d.id_Cliente
            LEFT JOIN Stock s ON s.id_producto_Stock = d.id_producto_Stock
            ORDER BY d.Fecha_DVtas DESC, d.id_detalle_DVtas DESC
        """
        df = fetch_df(sql)
        df = format_dataframe(df)
        st.dataframe(df, width="stretch")

        #st.dataframe(fetch_df(sql), width="stretch")

    else:
        # Datos para selects
        df_cli = fetch_df("SELECT id_cliente, Nomb_cliente FROM Clientes ORDER BY Nomb_cliente")
        cli_labels, cli_ids = df_to_select_options(df_cli, "id_cliente", ["Nomb_cliente"]) if not df_cli.empty else (["<sin clientes>"],[None])

        df_prod = fetch_df("SELECT id_producto_Stock, Descrip_Stock, Talle_Stock, Pcio_Vta_Stock, Pcio_Costo_Stock FROM Stock ORDER BY Descrip_Stock")
        prod_labels, prod_ids = df_to_select_options(df_prod, "id_producto_Stock", ["Descrip_Stock", "Talle_Stock"]) if not df_prod.empty else (["<sin productos>"],[None])

        def color_options(product_id: int):
            if product_id is None:
                return ["<SIN COLORES>"]
            d = fetch_df("SELECT Color_colores FROM Colores_Stock WHERE id_producto_Stock=? ORDER BY Color_colores", (int(product_id),))
            if d.empty:
                return ["<SIN COLORES>"]
            return d["Color_colores"].astype(str).str.upper().tolist()

        # ====================================================
        # INSERTAR
        # ====================================================
        if op == "Insertar":
            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                fecha = st.date_input("Fecha", value=date.today())
                id_cli = st.selectbox("Cliente", options=cli_ids, format_func=lambda x: cli_labels[cli_ids.index(x)] if x in cli_ids else "<sin clientes>")
            with c2:
                id_prod = st.selectbox("Producto", options=prod_ids, format_func=lambda x: prod_labels[prod_ids.index(x)] if x in prod_ids else "<sin productos>")
                id_prod = int(id_prod) if id_prod is not None else None
                talle_vta = st.text_input("Talle (venta) — opcional")
            with c3:
                colors = color_options(id_prod) if id_prod else ["<SIN COLORES>"]
                color_sel = st.selectbox("Color", options=colors)

            # Defaults de precios
            pcio_unit_default = 0.0
            pcio_costo_default = 0.0
            if id_prod:
                rowp = df_prod[df_prod["id_producto_Stock"] == id_prod].iloc[0]
                pcio_unit_default = float(rowp["Pcio_Vta_Stock"]) or 0.0
                pcio_costo_default = float(rowp["Pcio_Costo_Stock"]) or 0.0

            c4, c5, c6 = st.columns([2,2,2])
            with c4:
                cant = st.number_input("Cantidad", min_value=1, step=1, value=1)
            with c5:
                pcio_unit = st.number_input("Precio Unitario", min_value=0.0, step=0.1, value=pcio_unit_default)
            with c6:
                pcio_costo = st.number_input("Costo Unitario", min_value=0.0, step=0.1, value=pcio_costo_default)

            pcio_total = cant * pcio_unit
            st.info(f"Total: {pcio_total:.2f}")
            obs = st.text_area("Observaciones")
            estado = st.selectbox("Estado", ["A", "I"], index=0)

            if st.button("Guardar Detalle", type="primary"):
                color_norm = (color_sel or "").strip().upper()
                stock_ok = True

                if id_prod and color_norm and color_norm != "<SIN COLORES>":
                    df_stock = fetch_df(
                        "SELECT Cant_Stock_Colores FROM Colores_Stock WHERE id_producto_Stock=? AND UPPER(TRIM(Color_colores))=?",
                        (id_prod, color_norm)
                    )
                    if df_stock.empty:
                        st.error("❌ No se encontró stock para este producto/color.")
                        stock_ok = False
                    else:
                        stock_actual = int(df_stock.iloc[0]["Cant_Stock_Colores"])
                        if stock_actual <= 0:
                            st.warning(f"⚠️ Sin stock para '{color_norm}'.")
                            stock_ok = False
                        elif cant > stock_actual:
                            st.warning(f"⚠️ Stock insuficiente. Disponible: {stock_actual}, solicitado: {cant}.")
                            stock_ok = False

                if stock_ok:
                    fecha_str = fecha.isoformat()
                    cols = [
                        "Fecha_DVtas", "id_Cliente", "id_producto_Stock", "Color_DVtas",
                        "Talle_DVtas", "Cant_DVtas", "Pcio_Unitario_DVtas", "Pcio_Total_DVtas",
                        "Pcio_Costo_Unit_DVtas", "Obs_DVtas", "Estado_DVtas"
                    ]
                    qmarks = ",".join(["?"] * len(cols))
                    run_query(
                        f"INSERT INTO DetalleVentas ({','.join(cols)}) VALUES ({qmarks})",
                        (fecha_str, id_cli, id_prod, color_norm, talle_vta, int(cant), float(pcio_unit),
                         float(pcio_total), float(pcio_costo), obs, estado),
                    )
                    if id_prod and color_norm and color_norm != "<SIN COLORES>":
                        run_query(
                            """
                            UPDATE Colores_Stock
                            SET Cant_Stock_Colores = Cant_Stock_Colores - ?
                            WHERE id_producto_Stock=? AND UPPER(TRIM(Color_colores))=?
                            """,
                            (int(cant), id_prod, color_norm),
                        )
                    st.success("✅ Detalle agregado. Stock actualizado.")

        # ====================================================
        # EDITAR
        # ====================================================
        elif op == "Editar":
            df = fetch_df("SELECT * FROM DetalleVentas ORDER BY id_detalle_DVtas DESC")
            if df.empty:
                st.info("No hay detalles para editar")
                return
            ids = df["id_detalle_DVtas"].tolist()
            id_sel = st.selectbox("Detalle a editar (ID)", options=ids)
            det = df[df["id_detalle_DVtas"] == id_sel].iloc[0]

            c1, c2, c3 = st.columns([2,2,2])
            with c1:
                fecha_val = pd.to_datetime(det["Fecha_DVtas"]).date()
                fecha = st.date_input("Fecha", value=fecha_val)
                id_cli = st.selectbox("Cliente", options=cli_ids, index=(cli_ids.index(det["id_Cliente"]) if det["id_Cliente"] in cli_ids else 0), format_func=lambda x: cli_labels[cli_ids.index(x)] if x in cli_ids else "<sin clientes>")
            with c2:
                id_prod = det["id_producto_Stock"]
                id_prod = int(id_prod) if id_prod is not None else None
                id_prod = st.selectbox("Producto", options=prod_ids, index=(prod_ids.index(id_prod) if id_prod in prod_ids else 0), format_func=lambda x: prod_labels[prod_ids.index(x)] if x in prod_ids else "<sin productos>")
                id_prod = int(id_prod) if id_prod is not None else None
                talle_vta = st.text_input("Talle (venta)", det.get("Talle_DVtas", ""))
            with c3:
                colors = color_options(id_prod) if id_prod else ["<SIN COLORES>"]
                current_color = (det.get("Color_DVtas", "") or "").strip().upper()
                idx_color = colors.index(current_color) if current_color in colors else 0
                color_sel = st.selectbox("Color", options=colors, index=idx_color)

            c4, c5, c6 = st.columns([2,2,2])
            with c4:
                cant = st.number_input("Cantidad", min_value=1, step=1, value=int(det["Cant_DVtas"]))
            with c5:
                pcio_unit = st.number_input("Precio Unitario", min_value=0.0, step=0.1, value=float(det["Pcio_Unitario_DVtas"]))
            with c6:
                pcio_costo = st.number_input("Costo Unitario", min_value=0.0, step=0.1, value=float(det["Pcio_Costo_Unit_DVtas"]))

            pcio_total = cant * pcio_unit
            st.info(f"Total: {pcio_total:.2f}")
            obs = st.text_area("Observaciones", det.get("Obs_DVtas", ""))
            estado = st.selectbox("Estado", ["A", "I"], index=0 if det.get("Estado_DVtas", "A") == "A" else 1)

            if st.button("Actualizar Detalle", type="primary"):
                color_norm = (color_sel or "").strip().upper()
                stock_ok = True
                diferencia = cant - int(det["Cant_DVtas"])

                if id_prod and color_norm and color_norm != "<SIN COLORES>" and diferencia != 0:
                    df_stock = fetch_df(
                        "SELECT Cant_Stock_Colores FROM Colores_Stock WHERE id_producto_Stock=? AND UPPER(TRIM(Color_colores))=?",
                        (id_prod, color_norm)
                    )
                    if df_stock.empty:
                        st.error("❌ No se encontró stock para este producto/color.")
                        stock_ok = False
                    else:
                        stock_actual = int(df_stock.iloc[0]["Cant_Stock_Colores"])
                        if diferencia > 0 and stock_actual < diferencia:
                            st.warning(f"⚠️ Stock insuficiente. Disponible: {stock_actual}, necesitas {diferencia} adicionales.")
                            stock_ok = False

                if stock_ok:
                    fecha_str = fecha.isoformat()
                    run_query(
                        """
                        UPDATE DetalleVentas
                        SET Fecha_DVtas=?, id_Cliente=?, id_producto_Stock=?, Color_DVtas=?, Talle_DVtas=?,
                            Cant_DVtas=?, Pcio_Unitario_DVtas=?, Pcio_Total_DVtas=?, Pcio_Costo_Unit_DVtas=?,
                            Obs_DVtas=?, Estado_DVtas=?
                        WHERE id_detalle_DVtas=?
                        """,
                        (fecha_str, id_cli, id_prod, color_norm, talle_vta, int(cant), float(pcio_unit),
                         float(pcio_total), float(pcio_costo), obs, estado, id_sel),
                    )
                    if id_prod and color_norm and color_norm != "<SIN COLORES>" and diferencia != 0:
                        run_query(
                            """
                            UPDATE Colores_Stock
                            SET Cant_Stock_Colores = Cant_Stock_Colores - ?
                            WHERE id_producto_Stock=? AND UPPER(TRIM(Color_colores))=?
                            """,
                            (diferencia, id_prod, color_norm),
                        )
                    st.success("✅ Detalle actualizado y stock ajustado.")

        # ====================================================
        # ELIMINAR
        # ====================================================
        elif op == "Eliminar":
            df = fetch_df("SELECT * FROM DetalleVentas ORDER BY id_detalle_DVtas DESC")
            if df.empty:
                st.info("No hay registros para eliminar")
                return

            id_sel = st.selectbox("Detalle a eliminar (ID)", options=df["id_detalle_DVtas"].tolist())
            if id_sel and st.button("Eliminar Detalle", type="secondary"):
                det = df[df["id_detalle_DVtas"] == id_sel].iloc[0]

                id_prod = det["id_producto_Stock"]
                id_prod = int(id_prod) if id_prod is not None else None
                color_norm = (det.get("Color_DVtas", "") or "").strip().upper()
                cant = int(det["Cant_DVtas"])

                if id_prod and color_norm and color_norm != "<SIN COLORES>":
                    rows = run_query(
                        """
                        UPDATE Colores_Stock
                        SET Cant_Stock_Colores = Cant_Stock_Colores + ?
                        WHERE id_producto_Stock=? AND UPPER(TRIM(Color_colores))=?
                        """,
                        (cant, id_prod, color_norm),
                    )
                    if rows == 0:
                        st.error(f"⚠️ No se encontró stock para el producto {id_prod} con color '{color_norm}'. No se devolvió stock.")
                    else:
                        st.success(f"🗑️ Detalle eliminado. Se devolvieron {cant} unidades al stock de '{color_norm}'.")

                run_query("DELETE FROM DetalleVentas WHERE id_detalle_DVtas=?", (id_sel,))

# =====================
# LISTA DE PRECIOS (consulta + descarga)
# =====================

def pagina_lista_precios():

    #st.text('Lista de Precios', width='content')

    sql = """
        SELECT s.id_producto_Stock,
               s.Descrip_Stock,
               s.Talle_Stock,
               c.Color_colores AS color_stock,
               c.Cant_Stock_Colores,
               s.Pcio_Vta_Stock
        FROM Stock s
        LEFT JOIN Colores_Stock c ON c.id_producto_Stock = s.id_producto_Stock
        ORDER BY s.Descrip_Stock COLLATE NOCASE, c.Color_colores COLLATE NOCASE
    """
    df = fetch_df(sql)
    df = format_dataframe(df, move_obs_stock=True)
    st.dataframe(df, width="stretch")


    # Descargar CSV
    csv_buf = StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label="Descargar CSV",
        data=csv_buf.getvalue(),
        file_name="lista_precios.csv",
        mime="text/csv",
    )

    # Descargar HTML (para imprimir bonito)
    html_table = df.to_html(index=False)
    html_doc = f"""
    <html>
    <head>
        <meta charset='utf-8'>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 6px 8px; font-size: 12px; }}
            th {{ background: #eef; }}
        </style>
    </head>
    <body>
        <h3>Lista de precios</h3>
        {html_table}
    </body>
    </html>
    """
    st.download_button(
        label="Descargar para imprimir (HTML)",
        data=html_doc.encode("utf-8"),
        file_name="lista_precios.html",
        mime="text/html",
    )


# =====================
# REPORTE DE VENTAS ENTRE FECHAS
# =====================

def reporte_ventas_entre_fechas():

    #st.text('Reporte de Ventas entre Fechas', width='content')

    # Selector de rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser mayor que la fecha de fin.")
        return

    if st.button("Consultar"):
        sql = """
            SELECT d.id_detalle_DVtas,
                   d.Fecha_DVtas,
                   cli.Nomb_cliente AS Cliente,
                   s.Descrip_Stock AS Producto,
                   d.Color_DVtas,
                   d.Talle_DVtas,
                   d.Cant_DVtas,
                   d.Pcio_Unitario_DVtas,
                   d.Pcio_Total_DVtas
            FROM DetalleVentas d
            LEFT JOIN Clientes cli ON cli.id_cliente = d.id_Cliente
            LEFT JOIN Stock s ON s.id_producto_Stock = d.id_producto_Stock
            WHERE d.Fecha_DVtas BETWEEN ? AND ?
            ORDER BY d.Fecha_DVtas ASC
        """
        params = (fecha_inicio.isoformat(), fecha_fin.isoformat())
        df = fetch_df(sql, params)

        if df.empty:
            st.info("No hay ventas en ese rango de fechas.")
        else:
            #df = fetch_df(sql, params)
            df = format_dataframe(df)
            st.dataframe(df, width="stretch")


            # Totales

            total_vendido = df["Pcio_Total_DVtas"].sum()
            total_cantidad = df["Cant_DVtas"].sum()

            # Aseguramos que sea float
            try:
                total_vendido_num = float(total_vendido)
            except (ValueError, TypeError):
                total_vendido_num = 0.0

            st.success(f"Total vendido: ${total_vendido_num:,.2f} — Cantidad de artículos: {total_cantidad}")
            
            # Descarga CSV
            csv_buf = StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button(
                label="Descargar CSV",
                data=csv_buf.getvalue(),
                file_name="ventas_entre_fechas.csv",
                mime="text/csv",
            )


#===========================
# Clientes Inactivos
#===========================

def proceso_clientes_inactivos():
    st.header("Proceso de Clientes Inactivos")

    # Selección de rango de fechas
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("Fecha inicio", value=date.today().replace(day=1))
    with col2:
        fecha_fin = st.date_input("Fecha fin", value=date.today())

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser mayor que la fecha de fin.")
        return

    if st.button("Ejecutar Proceso", type="primary"):
        fecha_ini = fecha_inicio.isoformat()
        fecha_fin_str = fecha_fin.isoformat()

        # 1) Clientes que NO compraron en el rango → inactivar (Estado_Cliente='I')
        run_query(
            """
            UPDATE Clientes
            SET Estado_Cliente = 'I'
            WHERE id_cliente NOT IN (
                SELECT DISTINCT id_Cliente
                FROM DetalleVentas
                WHERE Fecha_DVtas BETWEEN ? AND ?
            )
            """,
            (fecha_ini, fecha_fin_str),
        )

        # 2) Clientes inactivos que SÍ compraron en el rango → reactivar (Estado_Cliente='A')
        run_query(
            """
            UPDATE Clientes
            SET Estado_Cliente = 'A'
            WHERE Estado_Cliente = 'I'
              AND id_cliente IN (
                  SELECT DISTINCT id_Cliente
                  FROM DetalleVentas
                  WHERE Fecha_DVtas BETWEEN ? AND ?
              )
            """,
            (fecha_ini, fecha_fin_str),
        )

        st.success("Proceso ejecutado: se actualizaron los estados de los clientes.")

    # 3) Consulta de clientes inactivos
    st.subheader("Clientes Inactivos")
    df_inactivos = fetch_df("SELECT id_cliente, Nomb_cliente, Estado_Cliente FROM Clientes WHERE Estado_Cliente='I' ORDER BY Nomb_cliente")

    if df_inactivos.empty:
        st.info("No hay clientes inactivos.")
    else:
        st.dataframe(df_inactivos, width="stretch")

        # Exportar a CSV
        csv_buf = StringIO()
        df_inactivos.to_csv(csv_buf, index=False)
        st.download_button(
            label="Descargar CSV de Clientes Inactivos",
            data=csv_buf.getvalue(),
            file_name="clientes_inactivos.csv",
            mime="text/csv",
        )



#===========================
# Dashboard
#===========================

def dashboard_ventas():
    st.header("Dashboard de Ventas")

    # ======================
    # Selección de rango de fechas
    # ======================
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input("📅 Fecha inicio", value=date(date.today().year, 1, 1))
    with col2:
        fecha_fin = st.date_input("📅 Fecha fin", value=date.today())

    if fecha_inicio > fecha_fin:
        st.error("La fecha de inicio no puede ser mayor que la fecha de fin.")
        return

    # ======================
    # DATOS BASE
    # ======================
    df = fetch_df("""
        SELECT d.Fecha_DVtas,
               d.Pcio_Total_DVtas,
               d.Pcio_Costo_Unit_DVtas,
               d.Cant_DVtas,
               s.Descrip_Stock AS Producto
        FROM DetalleVentas d
        LEFT JOIN Stock s ON d.id_producto_Stock = s.id_producto_Stock
        WHERE d.Fecha_DVtas BETWEEN ? AND ?
        ORDER BY d.Fecha_DVtas
    """, (fecha_inicio.isoformat(), fecha_fin.isoformat()))

    df_clientes = fetch_df("SELECT Estado_Cliente, COUNT(*) as Cantidad FROM Clientes GROUP BY Estado_Cliente")

    if df.empty:
        st.info("No hay datos de ventas para el rango seleccionado.")
        return

    # Convertir fechas
    df["Fecha_DVtas"] = pd.to_datetime(df["Fecha_DVtas"])
    df["Mes"] = df["Fecha_DVtas"].dt.to_period("M").astype(str)

    # ======================
    # KPIs - Métricas principales
    # ======================
    total_ventas = df["Pcio_Total_DVtas"].sum()
    total_costos = (df["Pcio_Costo_Unit_DVtas"] * df["Cant_DVtas"]).sum()
    ingreso_neto = total_ventas - total_costos

    clientes_activos = int(df_clientes.loc[df_clientes["Estado_Cliente"] == "A", "Cantidad"].sum()) if not df_clientes.empty else 0
    clientes_inactivos = int(df_clientes.loc[df_clientes["Estado_Cliente"] == "I", "Cantidad"].sum()) if not df_clientes.empty else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💲 Total Ventas", f"${total_ventas:,.2f}")
    with col2:
        st.metric("💰 Total Costos", f"${total_costos:,.2f}")
    with col3:
        st.metric("📈 Ingreso Neto", f"${ingreso_neto:,.2f}")

    col4, col5 = st.columns(2)
    with col4:
        st.metric("👥 Clientes Activos", clientes_activos)
    with col5:
        st.metric("💤 Clientes Inactivos", clientes_inactivos)

    st.markdown("---")

    # ======================
    # 1) Ventas Totales por Mes (Gráfico de Líneas + CSV)
    # ======================
    st.subheader("Ventas Totales por Mes")
    ventas_mes = df.groupby("Mes")["Pcio_Total_DVtas"].sum().reset_index()

    fig, ax = plt.subplots()
    ax.plot(ventas_mes["Mes"], ventas_mes["Pcio_Total_DVtas"], marker="o")
    ax.set_title("Ventas Totales por Mes")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Total Ventas ($)")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    csv_mes = StringIO()
    ventas_mes.to_csv(csv_mes, index=False)
    st.download_button("Descargar CSV Ventas por Mes", csv_mes.getvalue(), "ventas_por_mes.csv", "text/csv")

    # ======================
    # 2) Evolución de Ingreso Neto por Mes (Línea + Barras Apiladas + CSV)
    # ======================
    st.subheader("Ingreso Neto por Mes")

    # Calcular ingreso neto
    df["Ingreso_Neto"] = df["Pcio_Total_DVtas"] - (df["Pcio_Costo_Unit_DVtas"] * df["Cant_DVtas"])

    ingreso_mes = df.groupby("Mes").agg({
        "Pcio_Total_DVtas": "sum",
        "Pcio_Costo_Unit_DVtas": "sum",  # ojo, vamos a corregir abajo
        "Cant_DVtas": "sum",
        "Ingreso_Neto": "sum"
    }).reset_index()

    # Calcular costos totales correctamente
    #costos_mes = df.groupby("Mes").apply(lambda x: (x["Pcio_Costo_Unit_DVtas"] * x["Cant_DVtas"]).sum()).reset_index(name="Total_Costos")
    #ingreso_mes = ingreso_mes.merge(costos_mes, on="Mes", how="left")

    # Calculamos costos por mes
    costos_mes = (
    df.assign(Costo_Total=df["Pcio_Costo_Unit_DVtas"] * df["Cant_DVtas"])
      .groupby("Mes", as_index=False)["Costo_Total"].sum()
      .rename(columns={"Costo_Total": "Total_Costos"})
                )

    # Le agregamos esa info a ingreso_mes
    ingreso_mes = ingreso_mes.merge(costos_mes, on="Mes", how="left")

    # Línea de ingreso neto
    fig6, ax6 = plt.subplots()
    ax6.plot(ingreso_mes["Mes"], ingreso_mes["Ingreso_Neto"], marker="o", color="green", label="Ingreso Neto")
    ax6.set_title("Ingreso Neto por Mes (Línea)")
    ax6.set_xlabel("Mes")
    ax6.set_ylabel("Ingreso Neto ($)")
    plt.xticks(rotation=45)
    ax6.legend()
    st.pyplot(fig6)

    # Barras apiladas Ventas vs Costos
    fig7, ax7 = plt.subplots()
    ax7.bar(ingreso_mes["Mes"], ingreso_mes["Pcio_Total_DVtas"], label="Ventas", color="skyblue")
    ax7.bar(ingreso_mes["Mes"], ingreso_mes["Total_Costos"], label="Costos", color="salmon")
    ax7.set_title("Ventas vs Costos por Mes (Barras Apiladas)")
    ax7.set_xlabel("Mes")
    ax7.set_ylabel("Montos ($)")
    plt.xticks(rotation=45)
    ax7.legend()
    st.pyplot(fig7)

    # Descargar CSV
    csv_ing = StringIO()
    ingreso_mes[["Mes", "Pcio_Total_DVtas", "Total_Costos", "Ingreso_Neto"]].to_csv(csv_ing, index=False)
    st.download_button(
        "Descargar CSV Ingreso Neto por Mes",
        csv_ing.getvalue(),
        "ingreso_neto_por_mes.csv",
        "text/csv",
    )



    # ======================
    # 3) Rendimiento de Ventas (Venta vs Costo - Torta)
    # ======================
    st.subheader("Rendimiento de Ventas (Venta vs Costo)")
    fig2, ax2 = plt.subplots()
    ax2.pie([total_ventas, total_costos], labels=["Venta", "Costo"], autopct="%1.1f%%", startangle=90)
    ax2.set_title("Proporción Ventas vs Costos")
    st.pyplot(fig2)

    # ======================
    # 4) Ventas por Producto (Barras + CSV)
    # ======================
    st.subheader("Ventas por Producto")
    ventas_producto = df.groupby("Producto")["Pcio_Total_DVtas"].sum().reset_index()

    fig3, ax3 = plt.subplots()
    ax3.bar(ventas_producto["Producto"], ventas_producto["Pcio_Total_DVtas"])
    ax3.set_title("Ventas Totales por Producto")
    ax3.set_xlabel("Producto")
    ax3.set_ylabel("Total Ventas ($)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig3)

    csv_prod = StringIO()
    ventas_producto.to_csv(csv_prod, index=False)
    st.download_button("Descargar CSV Ventas por Producto", csv_prod.getvalue(), "ventas_por_producto.csv", "text/csv")

    # ======================
    # 5) Rentabilidad por Producto (Barras + CSV)
    # ======================
    st.subheader("Rentabilidad por Producto (Venta - Costo)")
    rentab_prod = df.groupby("Producto")["Ingreso_Neto"].sum().reset_index()

    fig4, ax4 = plt.subplots()
    ax4.bar(rentab_prod["Producto"], rentab_prod["Ingreso_Neto"], color="green")
    ax4.set_title("Ingreso Neto por Producto")
    ax4.set_xlabel("Producto")
    ax4.set_ylabel("Ingreso Neto ($)")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig4)

    csv_rentab = StringIO()
    rentab_prod.to_csv(csv_rentab, index=False)
    st.download_button("Descargar CSV Rentabilidad por Producto", csv_rentab.getvalue(), "rentabilidad_por_producto.csv", "text/csv")

    # ======================
    # 6) Clientes Activos vs Inactivos (Torta + CSV)
    # ======================
    st.subheader("Distribución de Clientes (Activos vs Inactivos)")
    if not df_clientes.empty:
        fig5, ax5 = plt.subplots()
        ax5.pie(df_clientes["Cantidad"], labels=df_clientes["Estado_Cliente"], autopct="%1.1f%%", startangle=90)
        ax5.set_title("Clientes Activos (A) vs Inactivos (I)")
        st.pyplot(fig5)

        csv_clientes = StringIO()
        df_clientes.to_csv(csv_clientes, index=False)
        st.download_button("Descargar CSV Clientes Activos/Inactivos", csv_clientes.getvalue(), "clientes_activos_inactivos.csv", "text/csv")

#===========================
# HERRAMIENTAS
#===========================

def herramientas():
    st.subheader("Herramientas de la Base de Datos")

    opcion = st.radio("Seleccione una opción:", ["Back-up", "Restore"], key="herramientas_radio")

    if opcion == "Back-up":
        if st.button("Generar Backup", key="btn_backup"):
            backup_file = backup_db()
            st.success(f"Backup generado: {backup_file}")

            # Botón de descarga directa
            with open(backup_file, "rb") as f:
                st.download_button(
                    label="⬇️ Descargar Backup",
                    data=f,
                    file_name=os.path.basename(backup_file),
                    mime="application/octet-stream"
                )

    elif opcion == "Restore":
        archivos = os.listdir(BACKUP_DIR)
        archivos = [f for f in archivos if f.endswith(".db")]

        if archivos:
            backup_file = st.selectbox("Seleccione backup a restaurar:", archivos)
            if st.button("Restaurar", key="btn_restore"):
                if restore_db(os.path.join(BACKUP_DIR, backup_file)):
                    st.success(f"Base de datos restaurada desde {backup_file}")
                    st.warning("⚠️ Es recomendable reiniciar la aplicación después de un restore.")
        else:
            st.info("No hay backups disponibles.")


# =====================
# MENÚ PRINCIPAL
# =====================

menu = st.sidebar.selectbox(
    "Menú Principal",
    ["Clientes", "Proveedores", "Stock", "DetalleVentas", "Lista de Precios", "Reporte Ventas", "Clientes Inactivos", "Dashboard de ventas", "Herramientas", "Salir"],
    key="menu_principal"
)

header_placeholder = st.empty()

if menu == "Clientes":
    header_placeholder.markdown("<div class='app-header'>👥Gestión de Clientes</div>", unsafe_allow_html=True)
    crud_clientes()

elif menu == "Proveedores":
    header_placeholder.markdown("<div class='app-header'>Gestión de Proveedores</div>", unsafe_allow_html=True)
    crud_proveedores()

elif menu == "Stock":
    header_placeholder.markdown("<div class='app-header'>Gestión de Stock</div>", unsafe_allow_html=True)
    crud_stock()

elif menu == "DetalleVentas":
    header_placeholder.markdown("<div class='app-header'>Gestión de Detalle de Ventas</div>", unsafe_allow_html=True)
    crud_detalleventas()

elif menu == "Lista de Precios":
    header_placeholder.markdown("<div class='app-header'>Lista de Precios</div>", unsafe_allow_html=True)
    pagina_lista_precios()

elif menu == "Reporte Ventas":
    header_placeholder.markdown("<div class='app-header'>Reporte de Ventas entre Fechas</div>", unsafe_allow_html=True)
    reporte_ventas_entre_fechas()

elif menu == "Clientes Inactivos":
    proceso_clientes_inactivos()

elif menu == "Dashboard de ventas":
    dashboard_ventas()

elif menu == "Herramientas":
    herramientas()

elif menu == "Salir":
    header_placeholder.markdown("<div class='app-header'>Salir</div>", unsafe_allow_html=True)
    try:
        conn = get_connection()
        conn.close()
    except Exception:
        pass
    st.info("Base cerrada. Podés cerrar esta pestaña.")
    st.stop()


