@echo off
REM =====================================
REM Resetear base SQLite con datos de prueba
REM =====================================

set DB_FILE=ventas.db
set SQL_FILE=reset_db.sql

echo ------------------------------
echo Reseteando base de datos: %DB_FILE%
echo Usando script: %SQL_FILE%
echo ------------------------------

REM Borrar DB vieja si existe
if exist %DB_FILE% (
    del %DB_FILE%
    echo Base de datos anterior eliminada.
)

REM Ejecutar script SQL con sqlite3
sqlite3 %DB_FILE% < %SQL_FILE%

echo ------------------------------
echo Reset completado.
echo Ahora podés abrir la app Streamlit.
echo ------------------------------
pause
