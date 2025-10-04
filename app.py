import streamlit as st
from datetime import datetime
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

# === FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS (sin tarjeta) ===
def guardar_en_sheet(datos):
    try:
        import gspread
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
        sheet.append_row(datos)
        return True
    except Exception as e:
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

    # === NAVEGACIÓN Y LÓGICA DE PÁGINAS ===
    if "inicio" in st.session_state and st.session_state["inicio"]:
        st.session_state.pagina = "inicio"
    elif "tareas" in st.session_state and st.session_state["tareas"]:
        st.session_state.pagina = "tareas"
    elif "asesoria" in st.session_state and st.session_state["asesoria"]:
        st.session_state.pagina = "asesoria"
    elif "tutor" in st.session_state and st.session_state["tutor"]:
        st.session_state.pagina = "tutor"
    elif "chat" in st.session_state and st.session_state["chat"]:
        st.session_state.pagina = "chat"
    else:
        st.session_state.pagina = st.session_state.get("pagina", "inicio")

    # Barra de navegación
    st.markdown("---")
    cols = st.columns(5)
    with cols[0]:
        st.button("🏠 Inicio", key="inicio", use_container_width=True)
    with cols[1]:
        st.button("✅ Tareas", key="tareas", use_container_width=True)
    with cols[2]:
        st.button("🆘 Asesoría", key="asesoria", use_container_width=True)
    with cols[3]:
        st.button("💬 Chat", key="chat", use_container_width=True)
    with cols[4]:
        st.button("👨‍🏫 Tutor" if st.session_state.rol == "estudiante" else "📊 Mis tutorías", key="tutor", use_container_width=True)

    # === RENDERIZAR LA PÁGINA ACTUAL ===
    pagina = st.session_state.pagina

    if pagina == "inicio":
        st.subheader("🎓 Bienvenido/a a Acompáñame")
        st.info("Selecciona una opción en la barra inferior para comenzar.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Mis tareas", use_container_width=True):
                st.session_state.pagina = "tareas"
                st.rerun()
        with col2:
            if st.button("🆘 Solicitar asesoría", use_container_width=True):
                st.session_state.pagina = "asesoria"
                st.rerun()

    elif pagina == "tareas":
        st.subheader("📌 Mis tareas")
        if "tareas_usuario" not in st.session_state:
            st.session_state.tareas_usuario = []
        
        with st.form("añadir_tarea"):
            nombre_tarea = st.text_input("Nombre de la tarea")
            fecha_limite = st.date_input("Fecha límite")
            submit = st.form_submit_button("➕ Añadir tarea")
            if submit and nombre_tarea:
                st.session_state.tareas_usuario.append({
                    "id": len(st.session_state.tareas_usuario) + 1,
                    "nombre": nombre_tarea,
                    "fecha_limite": str(fecha_limite),
                    "completada": False
                })
                st.success("✅ Tarea añadida")
                st.rerun()
        
        pendientes = [t for t in st.session_state.tareas_usuario if not t["completada"]]
        if pendientes:
            st.markdown("### Tareas pendientes")
            for t in pendientes:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{t['nombre']}** | 📅 {t['fecha_limite']}")
                with col2:
                    if st.button("✅", key=f"comp_{t['id']}"):
                        t["completada"] = True
                        st.rerun()
        else:
            st.success("¡No tienes tareas pendientes!")

    elif pagina == "asesoria" and st.session_state.rol == "estudiante":
        st.subheader("🆘 Solicitar asesoría")
        tutor_nombre = TUTORES[st.session_state.id_tutor]["nombre"]
        st.info(f"Tutor asignado: **{tutor_nombre}**")
        
        with st.form("solicitud_asesoria"):
            mensaje = st.text_area("Describe tu necesidad (máx. 200 caracteres)", max_chars=200)
            submit = st.form_submit_button("📤 Enviar solicitud")
            if submit and mensaje:
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
                
                if guardar_en_sheet([
                    nueva_solicitud["id"],
                    nueva_solicitud["estudiante"],
                    nueva_solicitud["tutor_id"],
                    nueva_solicitud["mensaje"],
                    nueva_solicitud["fecha_envio"],
                    "",
                    "pendiente"
                ]):
                    st.success("✅ Solicitud enviada. Tu tutor será notificado.")
                else:
                    st.warning("⚠️ Solicitud guardada localmente.")
                st.rerun()

    elif pagina == "tutor":
        if st.session_state.rol == "tutor":
            st.subheader("📬 Solicitudes pendientes")
            mis_solicitudes = [s for s in st.session_state.solicitudes 
                              if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "pendiente"]
            
            if mis_solicitudes:
                for s in mis_solicitudes:
                    with st.container():
                        st.markdown(f"**Estudiante:** {s['estudiante']} ({s['estudiante_codigo']})")
                        st.markdown(f"**Mensaje:** {s['mensaje']}")
                        st.caption(f"Enviado: {s['fecha_envio']}")
                        if st.button("✅ Aceptar y abrir chat", key=f"aceptar_{s['id']}"):
                            s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            s["estado"] = "en_chat"
                            if s["id"] not in st.session_state.mensajes_chat:
                                st.session_state.mensajes_chat[s["id"]] = []
                            st.success("✅ Sesión iniciada. Usa la pestaña 'Chat'.")
                            st.rerun()
                        st.divider()
            else:
                st.info("No tienes solicitudes pendientes.")
        else:
            st.subheader("📋 Mis solicitudes")
            mis_solicitudes = [s for s in st.session_state.solicitudes if s["estudiante_codigo"] == st.session_state.codigo]
            if mis_solicitudes:
                for s in mis_solicitudes:
                    estado = "✅ Aceptada" if s["estado"] == "aceptada" else "⏳ Pendiente" if s["estado"] == "pendiente" else "💬 En chat"
                    st.markdown(f"**Tutor:** {TUTORES[s['tutor_id']]['nombre']} | **Estado:** {estado}")
                    st.caption(f"Enviado: {s['fecha_envio']}")
                    if s.get("fecha_aceptacion"):
                        st.caption(f"Aceptada: {s['fecha_aceptacion']}")
                    st.divider()
            else:
                st.info("No has enviado solicitudes.")

    elif pagina == "chat":
        st.subheader("💬 Chat de asesoría")
        if st.session_state.rol == "estudiante":
            chats_activos = [s for s in st.session_state.solicitudes 
                           if s["estudiante_codigo"] == st.session_state.codigo and s["estado"] == "en_chat"]
        else:
            chats_activos = [s for s in st.session_state.solicitudes 
                           if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "en_chat"]
        
        if chats_activos:
            solicitud = chats_activos[0]
            st.info(f"Conversación con: {'Tutor' if st.session_state.rol=='estudiante' else solicitud['estudiante']}")
            
            mensajes = st.session_state.mensajes_chat.get(solicitud["id"], [])
            for msg in mensajes:
                st.text(f"{msg['usuario']} ({msg['fecha']}): {msg['texto']}")
            
            with st.form(f"chat_{solicitud['id']}"):
                nuevo_msg = st.text_input("Tu mensaje")
                enviar = st.form_submit_button("Enviar")
                if enviar and nuevo_msg:
                    st.session_state.mensajes_chat[solicitud["id"]].append({
                        "usuario": st.session_state.nombre,
                        "texto": nuevo_msg,
                        "fecha": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
        else:
            st.info("No tienes conversaciones activas.")