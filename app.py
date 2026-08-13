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
    except Exception as e:
        st.error(f"⚠️ Error cargando credenciales de Supabase: {e}")
        return None

supabase = init_supabase()

# Diccionario de respaldo de Sedes por ID (según tu INSERT de SQL)
MAPA_SEDES = {
    1: "Sede Central",
    2: "Los Vencedores",
    3: "Atanasio Girardot",
    4: "Inmaculada Concepción",
    5: "Jorge Eliécer Gaitán",
    6: "San Luis",
    7: "San Jorge",
    8: "Tres de Julio",
    9: "Otra / Comunidad Externa"
}

# 3. Encabezado e Identidad Institucional
col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    rutas_logo = ["img/Logo-IETIPAM-1024x1024.jpg", "Logo-IETIPAM-1024x1024.jpg", "img/Logo-IETIPAM-1024x1024.png", "logo.jpg"]
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

# 4. Función para Cargar Datos (Soportando la columna 'atendido')
def cargar_reportes():
    columnas_estandar = [
        "id", "es_colegio", "sede_id", "Sede", "rol", "grado_texto", 
        "nombre_persona", "documento", "telefono", "barrio_direccion", 
        "tipo_estado", "necesidades", "detalle", "fecha_registro", "atendido"
    ]
    
    if supabase:
        try:
            res = supabase.table("reportes").select("*").execute()
            df_data = pd.DataFrame(res.data)
            
            if not df_data.empty:
                df_data["Sede"] = df_data["sede_id"].map(MAPA_SEDES).fillna("Otra / Comunidad Externa")
                if "atendido" not in df_data.columns:
                    df_data["atendido"] = False
                else:
                    df_data["atendido"] = df_data["atendido"].fillna(False).astype(bool)
                return df_data
        except Exception as e:
            st.error(f"Error consultando la base de datos: {e}")
            
    return pd.DataFrame(columns=columnas_estandar)

# Función aux para actualizar el estado en Supabase
def cambiar_estado_atendido(id_registro, estado_actual):
    if supabase and id_registro:
        try:
            supabase.table("reportes").update({"atendido": not estado_actual}).eq("id", id_registro).execute()
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Error actualizando estado: {e}")

df = cargar_reportes()

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

# 6. Filtrado Dinámico de Datos
df_filtered = df.copy()

if not df_filtered.empty:
    if sede_sel != "Todas":
        df_filtered = df_filtered[df_filtered["Sede"] == sede_sel]

    if filtro_comunidad == "🏫 Comunidad IETIPAM":
        df_filtered = df_filtered[df_filtered["es_colegio"] == True]
    elif filtro_comunidad == "🏡 Vecinos / Externos":
        df_filtered = df_filtered[df_filtered["es_colegio"] == False]

# 7. Tarjetas Métricas
m1, m2, m3, m4 = st.columns(4)

total_reg = len(df_filtered)
fam_bien = len(df_filtered[df_filtered["tipo_estado"].astype(str).str.contains("ESTOY_BIEN|BIEN", na=False)]) if not df_filtered.empty else 0
fam_ayuda = len(df_filtered[df_filtered["tipo_estado"].astype(str).str.contains("NECESITO_AYUDA|AYUDA", na=False)]) if not df_filtered.empty else 0
com_esc = len(df_filtered[df_filtered["es_colegio"] == True]) if not df_filtered.empty else 0

m1.metric(label="📋 Total Reportes", value=total_reg)
m2.metric(label="🟢 Familias A Salvo", value=fam_bien)
m3.metric(label="🤝 Necesitan Apoyo", value=fam_ayuda)
m4.metric(label="🏫 Comunidad Escolar", value=com_esc)

st.divider()

# 8. Pestañas de Trabajo (Agregada pestaña de Gestión Unificada con Check)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Consolidado General", 
    "🏫 Censo por Sede y Grado", 
    "📦 Logística de Apoyos y Víveres",
    "🟡 Ubicación de Familiares",
    "🛖 Afectación de Viviendas",
    "✅ Gestión y Seguimiento Unificado"
])

with tab1:
    st.subheader("Listado Consolidado de Reportes Recibidos")
    
    if not df_filtered.empty:
        # Añadir columna visual de estado verde/rojo para el consolidado
        df_display = df_filtered.copy()
        df_display["Estado Atendido"] = df_display["atendido"].apply(lambda x: "🟢 ATENDIDO / CONTACTADO" if x else "🔴 PENDIENTE POR ATENDER")
        
        cols_mostrar = ["Estado Atendido", "tipo_estado", "nombre_persona", "rol", "Sede", "grado_texto", "telefono", "barrio_direccion", "necesidades", "detalle", "fecha_registro"]
        cols_existentes = [c for c in cols_mostrar if c in df_display.columns]
        
        st.dataframe(df_display[cols_existentes], use_container_width=True)
    else:
        st.info("ℹ️ Aún no hay registros en la base de datos.")
    
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
    if not df_filtered.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("### Reportes por Sede Educativa")
            st.bar_chart(df_filtered["Sede"].value_counts())
        
        with col_b:
            st.write("### Reportes por Rol en la Comunidad")
            st.bar_chart(df_filtered["rol"].value_counts())
    else:
        st.info("ℹ️ Sin datos suficientes para generar gráficas.")

with tab3:
    st.subheader("Familias que Requieren Entrega de Apoyos o Víveres")
    if not df_filtered.empty:
        df_necesidad = df_filtered[df_filtered["tipo_estado"].astype(str).str.contains("NECESITO_AYUDA|AYUDA", na=False)]
        
        if not df_necesidad.empty:
            for idx, row in df_necesidad.iterrows():
                st_icon = "🟢" if row.get("atendido", False) else "🔴"
                with st.expander(f"{st_icon} {row.get('nombre_persona', 'N/A')} — {row.get('barrio_direccion', 'N/A')} (Sede: {row.get('Sede', 'N/A')})"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Teléfono:** {row.get('telefono', 'N/A')}")
                        st.write(f"**Rol / Grado:** {row.get('rol', 'N/A')} - {row.get('grado_texto', 'N/A')}")
                    with c2:
                        st.write(f"**Insumos solicitados:** {row.get('necesidades', [])}")
                        st.write(f"**Mensaje:** {row.get('detalle', 'Sin observaciones')}")
        else:
            st.success("🟢 No hay solicitudes de apoyo pendientes bajo el filtro seleccionado.")
    else:
        st.info("ℹ️ No hay solicitudes de apoyo registradas.")

with tab4:
    st.subheader("🟡 Ubicación y Búsqueda de Familiares")
    if not df_filtered.empty:
        df_busco = df_filtered[df_filtered["tipo_estado"].astype(str).str.contains("BUSCO_A_ALGUIEN|BUSCO", na=False)]
        
        if not df_busco.empty:
            for idx, row in df_busco.iterrows():
                st_icon = "🟢" if row.get("atendido", False) else "🟡"
                with st.expander(f"{st_icon} {row.get('nombre_persona', 'N/A')} — {row.get('barrio_direccion', 'N/A')} (Sede: {row.get('Sede', 'N/A')})"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Teléfono:** {row.get('telefono', 'N/A')}")
                        st.write(f"**Rol / Grado:** {row.get('rol', 'N/A')} - {row.get('grado_texto', 'N/A')}")
                    with c2:
                        st.warning(f"**Mensaje / Detalle de la Búsqueda:** {row.get('detalle', 'Sin observaciones')}")
        else:
            st.success("🟢 No hay registros activos de búsqueda de familiares.")
    else:
        st.info("ℹ️ No hay reportes de búsqueda de personas registrados.")

with tab5:
    st.subheader("🛖 Reportes de Afectación de Viviendas")
    if not df_filtered.empty:
        df_dano = df_filtered[df_filtered["tipo_estado"].astype(str).str.contains("REPORTAR_DANO|DANO|DAÑO", na=False)]
        
        if not df_dano.empty:
            for idx, row in df_dano.iterrows():
                st_icon = "🟢" if row.get("atendido", False) else "🔴"
                with st.expander(f"{st_icon} {row.get('nombre_persona', 'N/A')} — {row.get('barrio_direccion', 'N/A')} (Sede: {row.get('Sede', 'N/A')})"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Teléfono:** {row.get('telefono', 'N/A')}")
                        st.write(f"**Rol / Grado:** {row.get('rol', 'N/A')} - {row.get('grado_texto', 'N/A')}")
                    with c2:
                        st.error(f"**Detalle del Daño Reportado:** {row.get('detalle', 'Sin observaciones')}")
        else:
            st.success("🟢 No hay reportes de daños en viviendas bajo el filtro seleccionado.")
    else:
        st.info("ℹ️ No hay reportes de afectación registrados.")

# 9. PESTAÑA UNIFICADA DE ATENCIÓN Y SEGUIMIENTO CON CHECKS
with tab6:
    st.subheader("📋 Listado Unificado para Gestión de Casos Críticos")
    st.caption("Afectaciones prioritarias: Logística de Apoyos, Ubicación de Personas y Daños en Vivienda.")
    
    if not df_filtered.empty:
        # Filtrar unificado los 3 casos prioritarios
        filtro_casos = df_filtered["tipo_estado"].astype(str).str.contains("NECESITO_AYUDA|AYUDA|BUSCO_A_ALGUIEN|BUSCO|REPORTAR_DANO|DANO|DAÑO", na=False)
        df_gestion = df_filtered[filtro_casos]
        
        if not df_gestion.empty:
            for idx, row in df_gestion.iterrows():
                reg_id = row.get("id")
                atendido_val = bool(row.get("atendido", False))
                color_icono = "🟢 [ATENDIDO]" if atendido_val else "🔴 [PENDIENTE]"
                
                col_check, col_info = st.columns([1, 5])
                
                with col_check:
                    st.write("")
                    st.write("")
                    val_check = st.checkbox("¿Atendido?", value=atendido_val, key=f"chk_{reg_id}")
                    if val_check != atendido_val:
                        cambiar_estado_atendido(reg_id, atendido_val)
                
                with col_info:
                    with st.expander(f"{color_icono} {row.get('nombre_persona', 'N/A')} | {row.get('tipo_estado', 'N/A')} — {row.get('barrio_direccion', 'N/A')}"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Sede:** {row.get('Sede', 'N/A')}")
                            st.write(f"**Teléfono:** {row.get('telefono', 'N/A')}")
                            st.write(f"**Rol/Grado:** {row.get('rol', 'N/A')} - {row.get('grado_texto', 'N/A')}")
                        with c2:
                            st.write(f"**Insumos:** {row.get('necesidades', [])}")
                            st.write(f"**Detalle / Mensaje:** {row.get('detalle', 'Sin detalle')}")
                st.divider()
        else:
            st.success("🟢 No existen casos críticos pendientes por atender bajo este filtro.")
    else:
        st.info("ℹ️ No hay datos para procesar.")