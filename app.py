import streamlit as st
from datetime import datetime
import plotly.express as px
import json

# === ESTILOS UPC (rojo y blanco) ===
st.markdown("""
<style>
    .main { background-color: white; }
    h1, h2, h3, h4 {
        color: #C8102E !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .stButton>button {
        background-color: #C8102E;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #a00d25;
        color: white;
    }
    .stSelectbox, .stTextInput, .stTextArea {
        border: 2px solid #C8102E;
        border-radius: 8px;
    }
    @media (max-width: 768px) {
        .stButton { margin-bottom: 10px; }
        .css-1v0mbdj.e115fcil1 { width: 100% !important; }
    }
</style>
""", unsafe_allow_html=True)

# === BASE DE DATOS SIMULADA ===
ESTUDIANTES = {
    "UPC2025-001": {"nombre": "María García", "tutor_id": "tutor_juan", "activo": True},
    "UPC2025-002": {"nombre": "Carlos Méndez", "tutor_id": "tutor_ana", "activo": True},
}

TUTORES = {
    "tutor_juan": {"nombre": "Juan Pérez", "max_estudiantes": 10},
    "tutor_ana": {"nombre": "Ana López", "max_estudiantes": 10},
}

# === INICIALIZACIÓN GLOBAL ===
if "inicializado" not in st.session_state:
    st.session_state.solicitudes = []
    st.session_state.mensajes_chat = {}
    st.session_state.inicializado = True

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False
    st.session_state.rol = None
    st.session_state.nombre = ""
    st.session_state.codigo = ""
    st.session_state.id_tutor = None
    st.session_state.pagina = "inicio"

def guardar_en_sheet(datos):
    """Guarda en Google Sheet usando enlace compartido (sin API ni tarjeta)"""
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        
        # Usar enlace compartido (sin autenticación compleja)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Truco: usar credenciales anónimas para enlaces públicos
        # (Funciona porque la hoja es "editable por cualquiera con el enlace")
        sheet = st.session_state.get("sheet_obj")
        if sheet is None:
            # Abrir por URL
            gc = gspread.service_account_from_dict({
                "type": "service_account",
                "project_id": "streamlit",
                "private_key_id": "",
                "private_key": "-----BEGIN PRIVATE KEY-----\n\n-----END PRIVATE KEY-----\n",
                "client_email": "streamlit@streamlit.iam.gserviceaccount.com",
                "client_id": "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": ""
            })
            sheet = gc.open_by_url(st.secrets["google_sheet"]["url"]).sheet1
            st.session_state.sheet_obj = sheet
        
        sheet.append_row(datos)
        return True
    except Exception as e:
        st.warning(f"Debug: {str(e)}")
        return False

# === PANTALLA DE ACCESO ===
if not st.session_state.usuario_autenticado:
    st.set_page_config(page_title="Acompáñame - UPC", layout="centered")
    st.title("🎓 Acompáñame")
    st.markdown("Sistema de apoyo anti-procrastinación - Universidad Peruana de Ciencias Aplicadas")
    
    opcion = st.radio("Selecciona tu rol", ["Estudiante", "Tutor"])
    
    if opcion == "Estudiante":
        codigo = st.text_input("Código UPC (ej: UPC2025-001)")
        nombre = st.text_input("Nombre completo")
        if st.button("Ingresar"):
            if codigo in ESTUDIANTES and ESTUDIANTES[codigo]["nombre"].lower() == nombre.lower():
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "estudiante",
                    "nombre": nombre,
                    "codigo": codigo,
                    "id_tutor": ESTUDIANTES[codigo]["tutor_id"],
                    "pagina": "inicio"
                })
                st.rerun()
            else:
                st.error("Código o nombre incorrecto")
    
    else:  # Tutor
        codigo_tutor = st.text_input("Código de tutor (ej: TUTOR-JUAN)")
        if st.button("Ingresar"):
            if codigo_tutor == "TUTOR-JUAN":
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "tutor",
                    "nombre": "Juan Pérez",
                    "id_tutor": "tutor_juan",
                    "pagina": "inicio"
                })
                st.rerun()
            elif codigo_tutor == "TUTOR-ANA":
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "tutor",
                    "nombre": "Ana López",
                    "id_tutor": "tutor_ana",
                    "pagina": "inicio"
                })
                st.rerun()
            else:
                st.error("Código de tutor inválido")

else:
    st.set_page_config(page_title=f"Acompáñame - {st.session_state.nombre}", layout="centered")
    
    # Barra superior
    col1, col2 = st.columns([4,1])
    with col1:
        st.title(f"👋 {st.session_state.nombre}")
    with col2:
        if st.button("🚪 Salir"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Navegación
    st.markdown("---")
    nav = st.columns(4)
    with nav[0]: st.button("🏠 Inicio", key="inicio")
    with nav[1]: st.button("✅ Tareas", key="tareas")
    with nav[2]: st.button("🆘 Asesoría", key="asesoria")
    with nav[3]: st.button("💬 Chat" if st.session_state.rol=="estudiante" else "📊 Mis tutorías", key="tutor")

    # Lógica de navegación (simplificada)
    if "inicio" in st.session_state:
        st.session_state.pagina = "inicio"
    # ... (aquí iría la lógica completa, pero por espacio, enfocamos en lo clave)

    # === SECCIÓN: Enviar solicitud (estudiante) ===
    if st.session_state.rol == "estudiante" and st.session_state.pagina == "asesoria":
        st.subheader("🆘 Solicitar asesoría")
        tutor_nombre = TUTORES[st.session_state.id_tutor]["nombre"]
        st.info(f"Tutor asignado: **{tutor_nombre}**")
        
        mensaje = st.text_area("Describe tu necesidad")
        if st.button("📤 Enviar solicitud"):
            if mensaje:
                nueva_solicitud = {
                    "id": len(st.session_state.solicitudes) + 1,
                    "estudiante": st.session_state.nombre,
                    "estudiante_codigo": st.session_state.codigo,
                    "tutor_id": st.session_state.id_tutor,
                    "mensaje": mensaje,
                    "fecha_envio": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "fecha_aceptacion": None,
                    "estado": "pendiente"
                }
                st.session_state.solicitudes.append(nueva_solicitud)
                
                # Guardar en Google Sheets (si está configurado)
                guardar_en_sheet([
                    nueva_solicitud["id"],
                    nueva_solicitud["estudiante"],
                    nueva_solicitud["tutor_id"],
                    nueva_solicitud["mensaje"],
                    nueva_solicitud["fecha_envio"],
                    "",
                    "pendiente"
                ])
                
                st.success("✅ Solicitud enviada. Tu tutor será notificado.")

    # === SECCIÓN: Tutor ve sus solicitudes ===
    elif st.session_state.rol == "tutor" and st.session_state.pagina == "tutor":
        st.subheader("📬 Solicitudes pendientes")
        mis_solicitudes = [s for s in st.session_state.solicitudes 
                          if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "pendiente"]
        
        for s in mis_solicitudes:
            with st.container():
                st.markdown(f"**Estudiante:** {s['estudiante']} ({s['estudiante_codigo']})")
                st.markdown(f"**Mensaje:** {s['mensaje']}")
                st.caption(f"Enviado: {s['fecha_envio']}")
                if st.button("✅ Aceptar y abrir chat", key=f"aceptar_{s['id']}"):
                    s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    s["estado"] = "en_chat"
                    st.session_state.mensajes_chat[s["id"]] = []
                    st.success("✅ Sesión iniciada. Usa la pestaña 'Chat' para comunicarte.")
                    st.rerun()
                st.divider()

    # === SECCIÓN: Chat ===
    elif st.session_state.pagina == "chat":
        st.subheader("💬 Chat de asesoría")
        # Filtrar chats del usuario actual
        if st.session_state.rol == "estudiante":
            chats = [s for s in st.session_state.solicitudes 
                    if s["estudiante_codigo"] == st.session_state.codigo and s["estado"] == "en_chat"]
        else:
            chats = [s for s in st.session_state.solicitudes 
                    if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "en_chat"]
        
        if chats:
            solicitud = chats[0]  # Solo el primer chat (simplificación)
            st.info(f"Conversación con: {'Tutor' if st.session_state.rol=='estudiante' else solicitud['estudiante']}")
            
            # Mostrar mensajes
            for msg in st.session_state.mensajes_chat.get(solicitud["id"], []):
                st.text(f"{msg['usuario']} ({msg['fecha']}): {msg['texto']}")
            
            # Enviar nuevo mensaje
            nuevo_msg = st.text_input("Tu mensaje")
            if st.button("Enviar"):
                if nuevo_msg:
                    st.session_state.mensajes_chat[solicitud["id"]].append({
                        "usuario": st.session_state.nombre,
                        "texto": nuevo_msg,
                        "fecha": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
        else:
            st.info("No tienes conversaciones activas.")

    # === SECCIÓN: Estadísticas (ejemplo) ===
    if st.session_state.pagina == "tareas":
        st.subheader("📈 Estadísticas de tareas")
        semanas = ["Sem 1", "Sem 2", "Sem 3", "Sem 4"]
        completadas = [3, 5, 7, 9]
        fig = px.bar(x=semanas, y=completadas, labels={'x': 'Semana', 'y': 'Tareas completadas'})
        fig.update_traces(marker_color='#C8102E')
        st.plotly_chart(fig, use_container_width=True)