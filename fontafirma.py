

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os


import streamlit as st

import pandas as pd

def usar_sheets():
    return ("gcp_service_account" in st.secrets) and ("sheets" in st.secrets)



import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = st.secrets["sheets"]["SHEET_ID"]
WORKSHEET = st.secrets["sheets"].get("WORKSHEET", "datos")

def _ws():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        return sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=WORKSHEET, rows=2000, cols=20)

def cargar_desde_sheets():
    ws = _ws()
    df = get_as_dataframe(ws, evaluate_formulas=True, header=0)

    # Si está vacía o sin cabeceras → inicializa
    if df is None or df.empty or df.columns.tolist() == [0]:
        base = generar_departamentos()
        ws.clear()
        set_with_dataframe(ws, base)
        return base

    # Normaliza columnas
    cols = ["torre","piso","numero","departamento","estado","nombre","tipo_persona","observaciones"]
    for c in cols:
        if c not in df.columns: df[c] = ""
    df = df[cols].copy()
    df["piso"] = pd.to_numeric(df["piso"], errors="coerce").fillna(0).astype(int)
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce").fillna(0).astype(int)
    return df


def guardar_en_sheets(df):
    import gspread
    from google.oauth2.service_account import Credentials
    from gspread_dataframe import set_with_dataframe
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    sh = gspread.authorize(creds).open_by_key(st.secrets["sheets"]["SHEET_ID"])
    ws_name = st.secrets["sheets"].get("WORKSHEET", "datos")
    try:
        ws = sh.worksheet(ws_name)
    except Exception:
        ws = sh.add_worksheet(title=ws_name, rows=2000, cols=20)
    ws.clear()
    set_with_dataframe(ws, df)

if "gcp_service_account" in st.secrets and "sheets" in st.secrets:
    st.success("Secrets detectados ✅")
    st.write("Sheet ID:", st.secrets["sheets"]["SHEET_ID"])
else:
    st.warning("Aún no detecto Secrets. Revisa Settings → Secrets.")
# ----- Generar lista de departamentos -----
def generar_departamentos():
    deptos = []
    torres = {
        "A": [(1, 15), (2, 18), (3, 15)],
        "B": [(1, 14), (2, 14), (3, 13)],
        "C": [(1, 13), (2, 13), (3, 13)]
    }

    for torre, pisos in torres.items():
        for piso, max_num in pisos:
            for i in range(1, max_num + 1):
                depto_num = piso * 100 + i
                deptos.append({
                    "torre": torre,
                    "piso": piso,
                    "numero": depto_num,
                    "departamento": f"{torre}-{depto_num}",
                    "estado": "sin contacto",
                    "nombre": "",
                    "tipo_persona": "",
                    "observaciones": ""
                })
    return pd.DataFrame(deptos)

# ----- Cargar o inicializar base -----
def cargar_desde_sheets():
    import gspread
    from google.oauth2.service_account import Credentials
    from gspread_dataframe import get_as_dataframe, set_with_dataframe

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SHEET_ID = st.secrets["sheets"]["SHEET_ID"]
    WORKSHEET = st.secrets["sheets"].get("WORKSHEET", "datos")

    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET, rows=2000, cols=20)

    df = get_as_dataframe(ws, evaluate_formulas=True, header=0)
    if df is None or df.empty or df.columns.tolist() == [0]:
        base = generar_departamentos()
        ws.clear()
        set_with_dataframe(ws, base)
        return base

    cols = ["torre","piso","numero","departamento","estado","nombre","tipo_persona","observaciones"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols].copy()
    df["piso"] = pd.to_numeric(df["piso"], errors="coerce").fillna(0).astype(int)
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce").fillna(0).astype(int)
    return df

def guardar_en_sheets(df):
    import gspread
    from google.oauth2.service_account import Credentials
    from gspread_dataframe import set_with_dataframe

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SHEET_ID = st.secrets["sheets"]["SHEET_ID"]
    WORKSHEET = st.secrets["sheets"].get("WORKSHEET", "datos")

    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=WORKSHEET, rows=2000, cols=20)

    ws.clear()
    set_with_dataframe(ws, df)


# ----- Selección de ubicación -----
st.title("🧱 Control de Humedad - Edificio")


if "df" not in st.session_state:
    try:
        st.session_state.df = cargar_desde_sheets()
        st.success("Conectado a Google Sheets ✅")
    except Exception as e:
        st.error(f"No pude usar Google Sheets: {e}")
        st.stop()

df = st.session_state.df


col1, col2, col3 = st.columns(3)
torre_sel = col1.selectbox("Torre", ["A", "B", "C"])
piso_sel = col2.selectbox("Piso", [1, 2, 3])
# Obtener departamentos válidos
df_opciones = df[(df["torre"] == torre_sel) & (df["piso"] == piso_sel)]
deptos_disp = sorted(df_opciones["numero"].tolist())
numero_sel = col3.selectbox("Departamento", deptos_disp)
clave = f"{torre_sel}-{numero_sel}"

# Obtener registro actual
registro = df[df["departamento"] == clave].iloc[0]
idx = df[df["departamento"] == clave].index[0]

# ----- Editar información -----
st.markdown(f"### ✏️ Editar información de {clave}")
estado_opciones = ["humedad", "firmó", "sin humedad", "sin contacto", "no quiere firmar", "desocupado"]
tipo_opciones = ["", "dueño", "inquilino"]

estado = st.selectbox("Estado", estado_opciones, index=estado_opciones.index(registro["estado"]))
nombre = st.text_input("Nombre del vecino", value=registro["nombre"])
tipo = st.selectbox("¿Dueño o inquilino?", tipo_opciones, index=tipo_opciones.index(registro["tipo_persona"]))
obs = st.text_area("Observaciones", value=registro["observaciones"])

if st.button("💾 Guardar"):
    df.at[idx, "estado"] = estado
    df.at[idx, "nombre"] = nombre
    df.at[idx, "tipo_persona"] = tipo
    df.at[idx, "observaciones"] = obs
    st.session_state.df = df
    try:
        guardar_en_sheets(df)
        st.success("Cambios guardados en Google Sheets")
    except Exception as e:
        st.error(f"Error al guardar en Sheets: {e}")


# ----- Descargar CSV -----
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar CSV", csv, "estado_departamentos.csv", "text/csv")


# ----- Visualización como cuadrícula bonita -----
st.markdown("## 🏢 Mapa visual del edificio (cuadrícula)")
color_map = {
    "firmó": "#4CAF50",           # verde
    "humedad": "#2196F3",         # azul
    "sin humedad": "#BDBDBD",     # gris
    "sin contacto": "#FFC107",    # ámbar
    "desocupado": "#FFC108",    # ámbar
    "no quiere firmar": "#F44336" # rojo
}

st.markdown("""
<style>
.depto-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin-top: 20px;
}
.torre {
    text-align: center;
    font-weight: bold;
    font-size: 20px;
}
.piso {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    justify-content: center;
    margin-bottom: 12px;
}
.depto {
    width: 75px;
    height: 50px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Mostrar torres A, B, C como columnas
st.markdown('<div class="depto-grid">', unsafe_allow_html=True)

for torre in ["A", "B", "C"]:
    st.markdown(f'<div class="torre">{torre}</div>', unsafe_allow_html=True)
    
    pisos = sorted(df[df["torre"] == torre]["piso"].unique(), reverse=True)
    
    html = '<div>'
    for piso in pisos:
        piso_deptos = df[(df["torre"] == torre) & (df["piso"] == piso)]
        html += '<div class="piso">'
        for _, row in piso_deptos.iterrows():
            color = color_map.get(row["estado"], "#9E9E9E")
            html += f'<div class="depto" style="background-color: {color}">{row["departamento"]}</div>'
        html += '</div>'
    html += '</div>'
    
    st.markdown(html, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
