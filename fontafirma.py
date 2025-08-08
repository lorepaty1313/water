
import streamlit as st
import pandas as pd

# ========= Google Sheets =========
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import get_as_dataframe, set_with_dataframe

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Lee secrets (ya deben estar pegados en Cloud)
SHEET_ID = st.secrets["sheets"]["SHEET_ID"]
WORKSHEET = st.secrets["sheets"].get("WORKSHEET", "datos")

def _ws():
    """Abre (o crea) la worksheet."""
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    try:
        return sh.worksheet(WORKSHEET)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=WORKSHEET, rows=2000, cols=20)

# ========= Base de datos inicial =========
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

# ========= Persistencia: cargar / guardar =========
def cargar_desde_sheets():
    """Carga DF desde Sheets. Si está vacío, inicializa con la base."""
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
        if c not in df.columns:
            df[c] = ""
    df = df[cols].copy()
    df["piso"] = pd.to_numeric(df["piso"], errors="coerce").fillna(0).astype(int)
    df["numero"] = pd.to_numeric(df["numero"], errors="coerce").fillna(0).astype(int)
    for c in ["estado", "nombre", "tipo_persona", "observaciones"]:
        df[c] = df[c].fillna("").astype(str)
    
    return df

def guardar_en_sheets(df):
    ws = _ws()
    ws.clear()
    set_with_dataframe(ws, df)

# ========= App =========
st.title("🧱 Control de Humedad - Edificio")

# Diagnóstico rápido de secrets
if "gcp_service_account" in st.secrets and "sheets" in st.secrets:
    st.caption("Secrets detectados ✅  |  Sheet ID: " + st.secrets["sheets"]["SHEET_ID"])
else:
    st.error("No detecto Secrets. Ve a Settings → Secrets y pega el bloque TOML.")
    st.stop()

# Carga inicial desde Sheets
if "df" not in st.session_state:
    try:
        st.session_state.df = cargar_desde_sheets()
        st.success("Conectado a Google Sheets ✅")
    except Exception as e:
        st.error(f"No pude usar Google Sheets: {e}")
        st.stop()

df = st.session_state.df

# ======= Formulario de edición =======
col1, col2, col3 = st.columns(3)
torre_sel = col1.selectbox("Torre", ["A", "B", "C"])
piso_sel = col2.selectbox("Piso", [1, 2, 3])

df_opciones = df[(df["torre"] == torre_sel) & (df["piso"] == piso_sel)]
deptos_disp = sorted(df_opciones["numero"].tolist())
if not deptos_disp:
    st.warning("No hay departamentos para esa combinación (revisa la base).")
    st.stop()

numero_sel = col3.selectbox("Departamento", deptos_disp)
clave = f"{torre_sel}-{numero_sel}"

# Registro a editar
sel = df["departamento"] == clave
if not sel.any():
    st.warning(f"No encontré {clave} en la base.")
    st.stop()

idx = df.index[sel][0]
registro = df.loc[idx]

st.markdown(f"### ✏️ Editar información de {clave}")
estado_opciones = ["humedad", "firmó", "sin humedad", "sin contacto", "no quiere firmar", "desocupado"]
tipo_opciones = ["", "dueño", "inquilino"]

valor_estado = str(registro.get("estado", "") or "").strip()
if valor_estado not in estado_opciones:
    valor_estado = estado_opciones[0]  # "humedad" o ajusta si quieres otro default

valor_tipo = str(registro.get("tipo_persona", "") or "").strip()
if valor_tipo not in tipo_opciones:
    valor_tipo = ""  # opción en blanco

estado = st.selectbox("Estado", estado_opciones, index=estado_opciones.index(valor_estado))
nombre = st.text_input("Nombre del vecino", value=str(registro.get("nombre", "") or ""))
tipo = st.selectbox("¿Dueño o inquilino?", tipo_opciones, index=tipo_opciones.index(valor_tipo))
obs = st.text_area("Observaciones", value=str(registro.get("observaciones", "") or ""))

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

# Descargar CSV (por si quieres respaldo manual)
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Descargar CSV", csv, "estado_departamentos.csv", "text/csv")

# ======= Cuadrícula visual =======
st.markdown("## 🏢 Mapa visual del edificio (cuadrícula)")
color_map = {
    "firmó": "#4CAF50",        # verde
    "humedad": "#2196F3",      # azul
    "sin humedad": "#BDBDBD",  # gris
    "sin contacto": "#FFC107", # ámbar
    "desocupado": "#9E9E9E",   # gris medio
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
.torre { text-align: center; font-weight: bold; font-size: 20px; }
.piso { display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; margin-bottom: 12px; }
.depto {
    width: 75px; height: 50px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; color: white; font-weight: bold;
}
.legend { display:flex; gap:10px; flex-wrap:wrap; margin: 6px 0 14px 0; }
.legend-item { display:flex; align-items:center; gap:6px; }
.legend-swatch { width:14px; height:14px; border-radius:3px; display:inline-block; }
</style>
""", unsafe_allow_html=True)

# Leyenda
legend_html = '<div class="legend">'
for k, v in color_map.items():
    legend_html += f'<span class="legend-item"><span class="legend-swatch" style="background:{v}"></span>{k}</span>'
legend_html += '</div>'
st.markdown(legend_html, unsafe_allow_html=True)

# Render por torre/piso
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
            html += f'<div class="depto" style="background-color:{color}">{row["departamento"]}</div>'
        html += '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
