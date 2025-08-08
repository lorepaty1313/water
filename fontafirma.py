

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
if "df" not in st.session_state:
    st.session_state.df = generar_departamentos()

df = st.session_state.df

# ----- Selección de ubicación -----
st.title("🧱 Control de Humedad - Edificio")

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
    st.success("Cambios guardados")

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
    "Desocupado": "#FFC108",    # ámbar
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