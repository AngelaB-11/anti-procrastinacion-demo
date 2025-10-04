import streamlit as st
from datetime import datetime
import json

# === ESTILOS UPC ===
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
    @media (max-width: 768px) {
        .stButton { margin-bottom: 10px; }
    }
</style>
""", unsafe_allow_html=True)

# === BASE DE DATOS SIMULADA ===
ESTUDIANTES = {
    "UPC2025-001": {"nombre": "María García", "tutor_id": "tutor_juan", "activo": True},
    "UPC2025-002": {"nombre": "Carlos Méndez", "tutor_id": "tutor_ana", "activo": True},
    "UPC2025-003": {"nombre": "Lucía Rojas", "tutor_id": "tutor_juan", "activo": True},
}

TUTORES = {
    "tutor_juan": {"nombre": "Juan Pérez"},
    "tutor_ana": {"nombre": "Ana López"},
}

# === INICIALIZACIÓN GLOBAL ===
if "inicializado" not in st.session_state:
    st.session_state.solicitudes = []
    st.session_state.mensajes_chat = {}
    st.session_state.tareas_globales = {}  # tareas por estudiante
    st.session_state.estado_alumnos = {
        "UPC2025-001": "en_proceso",
        "UPC2025-002": "inicio",
        "UPC2025-003": "alta"
    }
    st.session_state.inicializado = True

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False
    st.session_state.rol = None
    st.session_state.nombre = ""
    st.session_state.codigo = ""
    st.session_state.id_tutor = None
    st.session_state.pagina = "inicio"

# === FUNCIÓN PARA GUARDAR EN GOOGLE SHEETS ===
def guardar_en_sheet(datos, hoja="solicitudes"):
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
        sheet = gc.open_by_url(st.secrets["google_sheet"]["url"]).worksheet(hoja)
        sheet.append_row(datos)
        return True
    except:
        return False

# === PANTALLA DE ACCESO ===
if not st.session_state.usuario_autenticado:
    st.set_page_config(page_title="Acompáñame - UPC", layout="centered")
    st.title("🎓 Acompáñame")
    st.markdown("Sistema de apoyo anti-procrastinación - UPC")
    
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
    
    else:
        codigo_tutor = st.text_input("Código de tutor (TUTOR-JUAN o TUTOR-ANA)")
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
                st.error("Código inválido")

else:
    st.set_page_config(page_title=f"Acompáñame - {st.session_state.nombre}", layout="centered")
    
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
    nav_cols = st.columns(5)
    with nav_cols[0]: st.button("🏠 Inicio", key="inicio", use_container_width=True)
    with nav_cols[1]: st.button("✅ Tareas", key="tareas", use_container_width=True)
    with nav_cols[2]: st.button("🆘 Asesoría", key="asesoria", use_container_width=True)
    with nav_cols[3]: st.button("💬 Chat", key="chat", use_container_width=True)
    with nav_cols[4]: st.button("👨‍🏫 Tutor" if st.session_state.rol=="estudiante" else "📊 Alumnos", key="tutor", use_container_width=True)

    # Determinar página
    if "inicio" in st.session_state and st.session_state["inicio"]: st.session_state.pagina = "inicio"
    elif "tareas" in st.session_state and st.session_state["tareas"]: st.session_state.pagina = "tareas"
    elif "asesoria" in st.session_state and st.session_state["asesoria"]: st.session_state.pagina = "asesoria"
    elif "tutor" in st.session_state and st.session_state["tutor"]: st.session_state.pagina = "tutor"
    elif "chat" in st.session_state and st.session_state["chat"]: st.session_state.pagina = "chat"
    else: st.session_state.pagina = st.session_state.get("pagina", "inicio")

    pagina = st.session_state.pagina

    # === INICIO ===
    if pagina == "inicio":
        st.subheader("🎓 Bienvenido/a a Acompáñame")
        st.info("Usa la barra inferior para navegar.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Mis tareas", use_container_width=True):
                st.session_state.pagina = "tareas"
                st.rerun()
        with col2:
            if st.button("🆘 Solicitar asesoría", use_container_width=True):
                st.session_state.pagina = "asesoria"
                st.rerun()

    # === TAREAS ===
    elif pagina == "tareas":
        st.subheader("📌 Mis tareas")
        codigo = st.session_state.codigo if st.session_state.rol == "estudiante" else "tutor"
        
        if codigo not in st.session_state.tareas_globales:
            st.session_state.tareas_globales[codigo] = []
        
        tareas_usuario = st.session_state.tareas_globales[codigo]
        
        with st.form("añadir_tarea"):
            nombre_tarea = st.text_input("Nombre de la tarea")
            fecha_limite = st.date_input("Fecha límite")
            submit = st.form_submit_button("➕ Añadir tarea")
            if submit and nombre_tarea:
                tareas_usuario.append({
                    "id": len(tareas_usuario) + 1,
                    "nombre": nombre_tarea,
                    "fecha_limite": str(fecha_limite),
                    "completada": False
                })
                st.success("✅ Tarea añadida")
                st.rerun()
        
        pendientes = [t for t in tareas_usuario if not t["completada"]]
        if pendientes:
            st.markdown("### Tareas pendientes")
            for t in pendientes:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**{t['nombre']}** | 📅 {t['fecha_limite']}")
                with col2:
                    if st.button("✅", key=f"comp_{t['id']}_{codigo}"):
                        t["completada"] = True
                        st.rerun()
        else:
            st.success("¡No tienes tareas pendientes!")

    # === SOLICITAR ASESORÍA ===
    elif pagina == "asesoria" and st.session_state.rol == "estudiante":
        st.subheader("🆘 Solicitar asesoría")
        tutor_nombre = TUTORES[st.session_state.id_tutor]["nombre"]
        st.info(f"Tutor asignado: **{tutor_nombre}**")
        
        with st.form("solicitud_asesoria"):
            mensaje = st.text_area("Describe tu necesidad", max_chars=200)
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
                st.rerun()

    # === PANEL DEL TUTOR (GESTIÓN DE ALUMNOS) ===
    elif pagina == "tutor" and st.session_state.rol == "tutor":
        st.subheader("📊 Mis alumnos")
        
        # Filtrar alumnos asignados a este tutor
        mis_alumnos = [cod for cod, datos in ESTUDIANTES.items() if datos["tutor_id"] == st.session_state.id_tutor]
        
        for cod in mis_alumnos:
            nombre_alumno = ESTUDIANTES[cod]["nombre"]
            estado_actual = st.session_state.estado_alumnos.get(cod, "inicio")
            
            st.markdown(f"### {nombre_alumno} ({cod})")
            col1, col2 = st.columns([3, 1])
            with col1:
                nuevo_estado = st.selectbox(
                    "Estado",
                    ["inicio", "en_proceso", "alta"],
                    index=["inicio", "en_proceso", "alta"].index(estado_actual),
                    key=f"estado_{cod}"
                )
            with col2:
                if st.button("💾 Guardar", key=f"guardar_{cod}"):
                    st.session_state.estado_alumnos[cod] = nuevo_estado
                    st.success("✅ Estado actualizado")
            
            # Mostrar tareas del alumno
            if cod in st.session_state.tareas_globales:
                tareas = st.session_state.tareas_globales[cod]
                completadas = sum(1 for t in tareas if t["completada"])
                total = len(tareas)
                if total > 0:
                    st.caption(f"Tareas: {completadas}/{total} completadas")
            st.divider()

    # === CHAT ===
    elif pagina == "chat":
        st.subheader("💬 Chat de asesoría")
        
        # Encontrar chats activos
        if st.session_state.rol == "estudiante":
            chats = [s for s in st.session_state.solicitudes 
                    if s["estudiante_codigo"] == st.session_state.codigo and s["estado"] == "en_chat"]
        else:
            chats = [s for s in st.session_state.solicitudes 
                    if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "en_chat"]
        
        if chats:
            solicitud = chats[0]
            otro_usuario = "Tutor" if st.session_state.rol == "estudiante" else solicitud["estudiante"]
            st.info(f"Conversación con: {otro_usuario}")
            
            # Mostrar mensajes
            mensajes = st.session_state.mensajes_chat.get(solicitud["id"], [])
            for msg in mensajes:
                st.text(f"{msg['usuario']} ({msg['fecha']}): {msg['texto']}")
            
            # Enviar mensaje
            with st.form(f"chat_form_{solicitud['id']}"):
                txt = st.text_input("Mensaje")
                if st.form_submit_button("Enviar"):
                    if txt:
                        st.session_state.mensajes_chat.setdefault(solicitud["id"], []).append({
                            "usuario": st.session_state.nombre,
                            "texto": txt,
                            "fecha": datetime.now().strftime("%H:%M")
                        })
                        st.rerun()
        else:
            st.info("No tienes conversaciones activas. Espera a que tu tutor acepte tu solicitud.")

    # === SOLICITUDES PARA TUTOR ===
    elif pagina == "tutor" and st.session_state.rol == "estudiante":
        st.subheader("📋 Mis solicitudes")
        mis_solicitudes = [s for s in st.session_state.solicitudes if s["estudiante_codigo"] == st.session_state.codigo]
        if mis_solicitudes:
            for s in mis_solicitudes:
                estado = "✅ Aceptada" if s["estado"] == "en_chat" else "⏳ Pendiente"
                st.markdown(f"**Tutor:** {TUTORES[s['tutor_id']]['nombre']} | **Estado:** {estado}")
                st.caption(f"Enviado: {s['fecha_envio']}")
                if s.get("fecha_aceptacion"):
                    st.caption(f"Aceptada: {s['fecha_aceptacion']}")
                st.divider()
        else:
            st.info("No has enviado solicitudes.")

    # === ACEPTAR SOLICITUDES (TUTOR) ===
    elif pagina == "asesoria" and st.session_state.rol == "tutor":
        st.subheader("📬 Solicitudes pendientes")
        mis_solicitudes = [s for s in st.session_state.solicitudes 
                          if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "pendiente"]
        for s in mis_solicitudes:
            st.markdown(f"**Estudiante:** {s['estudiante']} ({s['estudiante_codigo']})")
            st.markdown(f"**Mensaje:** {s['mensaje']}")
            if st.button("✅ Aceptar", key=f"aceptar_{s['id']}"):
                s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                s["estado"] = "en_chat"
                st.session_state.mensajes_chat[s["id"]] = []
                st.success("✅ Sesión iniciada. Usa la pestaña 'Chat'.")
                st.rerun()
            st.divider()