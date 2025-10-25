-- ========================================
-- RESET COMPLETO DE LA BASE (para pruebas)
-- ========================================

PRAGMA foreign_keys = OFF;

-- Borrar tablas si existen
DROP TABLE IF EXISTS DetalleVentas;
DROP TABLE IF EXISTS Colores_Stock;
DROP TABLE IF EXISTS Stock;
DROP TABLE IF EXISTS Proveedores;
DROP TABLE IF EXISTS Clientes;

PRAGMA foreign_keys = ON;

-- ====================
-- RECREAR TABLAS
-- ====================

CREATE TABLE Clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    Nomb_cliente TEXT NOT NULL,
    Domi_Cliente TEXT,
    Telef_Cliente TEXT,
    Obs_Cliente TEXT,
    Estado_Cliente TEXT DEFAULT 'A'
);

CREATE TABLE Proveedores (
    id_prove INTEGER PRIMARY KEY AUTOINCREMENT,
    Nomb_Prove TEXT NOT NULL,
    Domi_Prove TEXT,
    Telef_Prove TEXT,
    Obs_Prove TEXT,
    Estado_Prove TEXT DEFAULT 'A'
);

CREATE TABLE Stock (
    id_producto_Stock INTEGER PRIMARY KEY AUTOINCREMENT,
    Talle_Stock TEXT NOT NULL,
    Descrip_Stock TEXT,
    Pcio_Vta_Stock REAL NOT NULL,
    Pcio_Costo_Stock REAL NOT NULL,
    id_proveedor INTEGER,
    Obs_Stock TEXT,
    Estado_Stock TEXT DEFAULT 'A',
    FOREIGN KEY (id_proveedor) REFERENCES Proveedores(id_prove)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE Colores_Stock (
    id_colores INTEGER PRIMARY KEY AUTOINCREMENT,
    id_producto_Stock INTEGER NOT NULL,
    Color_colores TEXT NOT NULL,
    Cant_Stock_Colores INTEGER NOT NULL DEFAULT 0,
    Obs_Colores TEXT,
    Estado_Colores TEXT DEFAULT 'A',
    FOREIGN KEY (id_producto_Stock) REFERENCES Stock(id_producto_Stock)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE DetalleVentas (
    id_detalle_DVtas INTEGER PRIMARY KEY AUTOINCREMENT,
    Fecha_DVtas DATE NOT NULL,
    id_Cliente INTEGER NOT NULL,
    id_producto_Stock INTEGER NOT NULL,
    Talle_DVtas TEXT,
    Color_DVtas TEXT,
    Cant_DVtas INTEGER NOT NULL,
    Pcio_Unitario_DVtas REAL NOT NULL,
    Pcio_Total_DVtas REAL NOT NULL,
    Pcio_Costo_Unit_DVtas REAL NOT NULL,
    Obs_DVtas TEXT,
    Estado_DVtas TEXT DEFAULT 'A',
    FOREIGN KEY (id_producto_Stock) REFERENCES Stock(id_producto_Stock)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ====================
-- INSERTS DE PRUEBA
-- ====================

-- Clientes
INSERT INTO Clientes (Nomb_cliente, Domi_Cliente, Telef_Cliente, Obs_Cliente, Estado_Cliente)
VALUES
  ('Juan Pérez', 'Av. Siempreviva 123', '1111-2222', 'Cliente habitual', 'A'),
  ('María López', 'Calle Falsa 456', '3333-4444', 'Compra esporádicamente', 'A');

-- Proveedores
INSERT INTO Proveedores (Nomb_Prove, Domi_Prove, Telef_Prove, Obs_Prove, Estado_Prove)
VALUES
  ('Proveedor A', 'Av. Central 1000', '5555-6666', 'Mayorista de ropa', 'A'),
  ('Proveedor B', 'Calle Sur 200', '7777-8888', 'Proveedor secundario', 'A');

-- Productos (Stock)
INSERT INTO Stock (Talle_Stock, Descrip_Stock, Pcio_Vta_Stock, Pcio_Costo_Stock, id_proveedor, Obs_Stock, Estado_Stock)
VALUES
  ('M', 'Remera Básica', 500.00, 300.00, 1, 'Remera algodón', 'A'),
  ('42', 'Zapatilla Running', 12000.00, 8000.00, 2, 'Deportiva', 'A');

-- Colores
INSERT INTO Colores_Stock (id_producto_Stock, Color_colores, Cant_Stock_Colores, Obs_Colores, Estado_Colores)
VALUES
  (1, 'Rojo', 10, 'Remera roja', 'A'),
  (1, 'Azul', 5, 'Remera azul', 'A'),
  (2, 'Negro', 3, 'Zapatilla negra', 'A'),
  (2, 'Blanco', 2, 'Zapatilla blanca', 'A');

-- Ventas de ejemplo
INSERT INTO DetalleVentas (
    Fecha_DVtas, id_Cliente, id_producto_Stock, Talle_DVtas, Color_DVtas,
    Cant_DVtas, Pcio_Unitario_DVtas, Pcio_Total_DVtas, Pcio_Costo_Unit_DVtas,
    Obs_DVtas, Estado_DVtas
)
VALUES
  (date('now'), 1, 1, 'M', 'Rojo', 2, 500.00, 1000.00, 300.00, 'Compra en efectivo', 'A'),
  (date('now'), 2, 2, '42', 'Blanco', 1, 12000.00, 12000.00, 8000.00, 'Pago con tarjeta', 'A');
