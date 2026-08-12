import streamlit as st
import pandas as pd
import os
from supabase import create_client, Client

# 1. Configuración de la página
st.set_page_config(
    page_title="IETIPAM — Dashboard AQUÍ ESTOY",
    page_icon="🛡️",
    layout="wide"
)

# 2. Conexión a Supabase mediante Secrets
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

# Diccionario de Sedes IETIPAM para mapeo directo sin errores de consulta
MAPA_SEDES = {
    1: "Sede Central",
    2: "Los Vencedores",
    3: "Atanasio Girardot",
    4: "Inmaculada Concepción",
    5: "Jorge Eliécer Gaitán",
    6: "San Luis",
    7: "San Jorge",
    8: "Tres de Julio",
    9: "Comunidad / Vecinos"
}

# 3. Encabezado e Identidad Institucional
col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    rutas_logo = ["img/Logo-IETIPAM-1024x1024.png", "Logo-IETIPAM-1024x1024.png", "logo.png"]
    logo_encontrado = next((r for r in rutas_logo if os.path.exists(r)), None)
    if logo_encontrado:
        st.image(logo_encontrado, width=100)
    else:
        st.write("🛡️")

with col_titulo:
    st.title("INSTITUCIÓN EDUCATIVA TÉCNICO INDUSTRIAL PEDRO ANTONIO MOLINA")
    st.subheader("💙 Panel de Monitoreo y Censo Comunitario — AQUÍ ESTOY")
    st.caption("Santiago de Cali — Control y Logística de Apoyo por Sedes Educativas")

st.divider()

# 4. Función para Cargar Datos
# 4. Función para Cargar Datos Reales desde Supabase
def cargar_reportes():
    if supabase:
        try:
            # Consulta directa a la tabla de reportes
            res = supabase.table("reportes").select("*").execute()
            df = pd.DataFrame(res.data)
            
            if not df.empty:
                df["Sede"] = df["sede_id"].map(MAPA_SEDES).fillna("Otra Sede")
                return df
            else:
                # Si la tabla en Supabase está vacía, devuelve la estructura limpia con 0 filas
                return pd.DataFrame(columns=[
                    "id", "es_colegio", "sede_id", "Sede", "rol", "grado_texto", 
                    "nombre_persona", "documento", "telefono", "barrio_direccion", 
                    "tipo_estado", "necesidades", "detalle", "fecha_registro"
                ])
        except Exception as e:
            st.error(f"Error al consultar Supabase: {e}")
            
    # Retorno vacío si no hay cliente de Supabase
    return pd.DataFrame(columns=["tipo_estado", "nombre_persona", "rol", "Sede", "telefono"])

# 5. Barra Lateral de Filtros
with st.sidebar:
    st.header("🔍 Filtros de Consulta")
    sedes_disponibles = ["Todas"] + list(MAPA_SEDES.values())
    sede_sel = st.selectbox("Filtrar por Sede Educativa:", sedes_disponibles)
    filtro_comunidad = st.radio("Población:", ["Todos", "🏫 Comunidad IETIPAM", "🏡 Vecinos / Externos"])
    
    st.divider()
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Aplicar filtros
df_filtered = df.copy()
if sede_sel != "Todas":
    df_filtered = df_filtered[df_filtered["Sede"] == sede_sel]

if filtro_comunidad == "🏫 Comunidad IETIPAM":
    df_filtered = df_filtered[df_filtered["es_colegio"] == True]
elif filtro_comunidad == "🏡 Vecinos / Externos":
    df_filtered = df_filtered[df_filtered["es_colegio"] == False]

# 6. Tarjetas Métricas con Alta Legibilidad
m1, m2, m3, m4 = st.columns(4)

total_reg = len(df_filtered)
fam_bien = len(df_filtered[df_filtered["tipo_estado"].str.contains("ESTOY_BIEN", na=False)])
fam_ayuda = len(df_filtered[df_filtered["tipo_estado"].str.contains("NECESITO_AYUDA", na=False)])
com_esc = len(df_filtered[df_filtered["es_colegio"] == True])

m1.metric(label="📋 Total Reportes", value=total_reg)
m2.metric(label="🟢 Familias A Salvo", value=fam_bien)
m3.metric(label="🤝 Necesitan Apoyo", value=fam_ayuda)
m4.metric(label="🏫 Comunidad Escolar", value=com_esc)

st.divider()

# 7. Pestañas Principales
tab1, tab2, tab3 = st.tabs(["📋 Consolidado General", "🏫 Censo por Sede y Grado", "📦 Logística de Apoyos y Víveres"])

with tab1:
    st.subheader("Listado Consolidado de Reportes Recibidos")
    cols_mostrar = ["tipo_estado", "nombre_persona", "rol", "Sede", "grado_texto", "telefono", "barrio_direccion", "necesidades", "detalle", "fecha_registro"]
    cols_existentes = [c for c in cols_mostrar if c in df_filtered.columns]
    
    st.dataframe(df_filtered[cols_existentes], use_container_width=True)
    
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Informe en Excel / CSV",
        data=csv,
        file_name="reporte_censo_ietipam_aqui_estoy.csv",
        mime="text/csv",
        use_container_width=True
    )

with tab2:
    st.subheader("Caracterización por Sede y Rol")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("### Reportes por Sede Educativa")
        if "Sede" in df_filtered.columns and not df_filtered.empty:
            st.bar_chart(df_filtered["Sede"].value_counts())
    
    with col_b:
        st.write("### Reportes por Rol en la Comunidad")
        if "rol" in df_filtered.columns and not df_filtered.empty:
            st.bar_chart(df_filtered["rol"].value_counts())

with tab3:
    st.subheader("Familias que Requieren Entrega de Apoyos o Víveres")
    df_necesidad = df_filtered[df_filtered["tipo_estado"].str.contains("NECESITO_AYUDA", na=False)]
    
    if not df_necesidad.empty:
        for idx, row in df_necesidad.iterrows():
            with st.expander(f"🔴 {row.get('nombre_persona', 'N/A')} — {row.get('barrio_direccion', 'N/A')} (Sede: {row.get('Sede', 'N/A')})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Teléfono:** {row.get('telefono', 'N/A')}")
                    st.write(f"**Rol / Grado:** {row.get('rol', 'N/A')} - {row.get('grado_texto', 'N/A')}")
                with c2:
                    st.write(f"**Insumos solicitados:** {row.get('necesidades', [])}")
                    st.write(f"**Mensaje:** {row.get('detalle', 'Sin observaciones')}")
    else:
        st.success("🟢 No hay solicitudes de apoyo pendientes bajo el filtro seleccionado.")