import streamlit as st
import json, os
from datetime import datetime

# =============================
# 🧠 CONFIGURACIÓN Y ESTILOS
# =============================
st.set_page_config(page_title="Acompáñame - UPC", layout="centered")

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

# =============================
# 📂 ARCHIVO JSON COMPARTIDO
# =============================
DATA_FILE = "datos.json"

def cargar_datos():
    if not os.path.exists(DATA_FILE):
        data_inicial = {
            "solicitudes": [],
            "mensajes": {},
            "tareas": {},
            "estados": {
                "UPC2025-001": "en_proceso",
                "UPC2025-002": "inicio",
                "UPC2025-003": "alta"
            }
        }
        guardar_datos(data_inicial)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============================
# 👥 BASE DE USUARIOS
# =============================
ESTUDIANTES = {
    "UPC2025-001": {"nombre": "María García", "tutor_id": "tutor_juan", "activo": True},
    "UPC2025-002": {"nombre": "Carlos Méndez", "tutor_id": "tutor_ana", "activo": True},
    "UPC2025-003": {"nombre": "Lucía Rojas", "tutor_id": "tutor_juan", "activo": True},
}

TUTORES = {
    "tutor_juan": {"nombre": "Juan Pérez"},
    "tutor_ana": {"nombre": "Ana López"},
}

# =============================
# 🌐 SESIÓN DE USUARIO
# =============================
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False
    st.session_state.rol = None
    st.session_state.nombre = ""
    st.session_state.codigo = ""
    st.session_state.id_tutor = None
    st.session_state.pagina = "inicio"

# =============================
# 🟡 PANTALLA DE LOGIN
# =============================
if not st.session_state.usuario_autenticado:
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

# =============================
# 📌 APP PRINCIPAL
# =============================
else:
    col1, col2 = st.columns([4,1])
    with col1:
        st.title(f"👋 {st.session_state.nombre}")
    with col2:
        if st.button("🚪 Salir"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")
    nav_cols = st.columns(5)
    with nav_cols[0]: st.button("🏠 Inicio", key="inicio", use_container_width=True)
    with nav_cols[1]: st.button("✅ Tareas", key="tareas", use_container_width=True)
    with nav_cols[2]: st.button("🆘 Asesoría", key="asesoria", use_container_width=True)
    with nav_cols[3]: st.button("💬 Chat", key="chat", use_container_width=True)
    with nav_cols[4]: st.button("👨‍🏫 Tutor" if st.session_state.rol=="estudiante" else "📊 Alumnos", key="tutor", use_container_width=True)

    # Determinar página activa
    for p in ["inicio", "tareas", "asesoria", "chat", "tutor"]:
        if p in st.session_state and st.session_state[p]:
            st.session_state.pagina = p

    pagina = st.session_state.pagina
    data = cargar_datos()

    # =============================
    # 🏠 INICIO
    # =============================
    if pagina == "inicio":
        st.subheader("🎓 Bienvenido/a a Acompáñame")
        st.info("Usa la barra inferior para navegar.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Mis tareas", use_container_width=True):
                st.session_state.pagina = "tareas"; st.rerun()
        with col2:
            if st.button("🆘 Solicitar asesoría", use_container_width=True):
                st.session_state.pagina = "asesoria"; st.rerun()

    # =============================
    # 📌 TAREAS
    # =============================
    elif pagina == "tareas":
        codigo = st.session_state.codigo if st.session_state.rol == "estudiante" else st.session_state.id_tutor
        if codigo not in data["tareas"]:
            data["tareas"][codigo] = []
            guardar_datos(data)

        tareas_usuario = data["tareas"][codigo]

        with st.form("añadir_tarea"):
            nombre_tarea = st.text_input("Nombre de la tarea")
            fecha_limite = st.date_input("Fecha límite")
            submit = st.form_submit_button("➕ Añadir tarea")
            if submit and nombre_tarea:
                tareas_usuario.append({
                    "id": len(tareas_usuario)+1,
                    "nombre": nombre_tarea,
                    "fecha_limite": str(fecha_limite),
                    "completada": False
                })
                data["tareas"][codigo] = tareas_usuario
                guardar_datos(data)
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
                        guardar_datos(data)
                        st.rerun()
        else:
            st.success("¡No tienes tareas pendientes!")

    # =============================
    # 🆘 SOLICITAR ASESORÍA (ESTUDIANTE)
    # =============================
    elif pagina == "asesoria" and st.session_state.rol == "estudiante":
        st.subheader("🆘 Solicitar asesoría")
        tutor_nombre = TUTORES[st.session_state.id_tutor]["nombre"]
        st.info(f"Tutor asignado: **{tutor_nombre}**")
        
        with st.form("solicitud_asesoria"):
            mensaje = st.text_area("Describe tu necesidad", max_chars=200)
            submit = st.form_submit_button("📤 Enviar solicitud")
            if submit and mensaje:
                nueva_solicitud = {
                    "id": len(data["solicitudes"]) + 1,
                    "estudiante": st.session_state.nombre,
                    "estudiante_codigo": st.session_state.codigo,
                    "tutor_id": st.session_state.id_tutor,
                    "mensaje": mensaje,
                    "fecha_envio": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "fecha_aceptacion": None,
                    "estado": "pendiente"
                }
                data["solicitudes"].append(nueva_solicitud)
                guardar_datos(data)
                st.success("✅ Solicitud enviada")
                st.rerun()

    # =============================
    # 📬 SOLICITUDES (TUTOR)
    # =============================
    elif pagina == "asesoria" and st.session_state.rol == "tutor":
        st.subheader("📬 Solicitudes pendientes")
        pendientes = [s for s in data["solicitudes"] if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "pendiente"]
        for s in pendientes:
            st.markdown(f"**Estudiante:** {s['estudiante']} ({s['estudiante_codigo']})")
            st.markdown(f"**Mensaje:** {s['mensaje']}")
            if st.button("✅ Aceptar", key=f"aceptar_{s['id']}"):
                s["estado"] = "en_chat"
                s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                data["mensajes"][str(s["id"])] = []
                guardar_datos(data)
                st.success("✅ Solicitud aceptada. Ve al Chat.")
                st.rerun()
            st.divider()

    # =============================
    # 💬 CHAT
    # =============================
    elif pagina == "chat":
        if st.session_state.rol == "estudiante":
            chats = [s for s in data["solicitudes"] if s["estudiante_codigo"] == st.session_state.codigo and s["estado"] == "en_chat"]
        else:
            chats = [s for s in data["solicitudes"] if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "en_chat"]

        if chats:
            solicitud = chats[0]
            otro_usuario = "Tutor" if st.session_state.rol == "estudiante" else solicitud["estudiante"]
            st.subheader(f"💬 Chat con {otro_usuario}")

            mensajes = data["mensajes"].get(str(solicitud["id"]), [])
            for msg in mensajes:
                st.text(f"{msg['usuario']} ({msg['fecha']}): {msg['texto']}")

            with st.form(f"chat_form_{solicitud['id']}"):
                txt = st.text_input("Escribe un mensaje")
                if st.form_submit_button("Enviar") and txt:
                    mensajes.append({
                        "usuario": st.session_state.nombre,
                        "texto": txt,
                        "fecha": datetime.now().strftime("%H:%M")
                    })
                    data["mensajes"][str(solicitud["id"])] = mensajes
                    guardar_datos(data)
                    st.rerun()
        else:
            st.info("No tienes conversaciones activas.")

    # =============================
    # 👨‍🏫 PANEL TUTOR / 📋 MIS SOLICITUDES ESTUDIANTE
    # =============================
    elif pagina == "tutor" and st.session_state.rol == "tutor":
        st.subheader("📊 Mis alumnos")
        mis_alumnos = [cod for cod, datos in ESTUDIANTES.items() if datos["tutor_id"] == st.session_state.id_tutor]
        for cod in mis_alumnos:
            nombre = ESTUDIANTES[cod]["nombre"]
            estado_actual = data["estados"].get(cod, "inicio")
            nuevo_estado = st.selectbox(
                f"Estado de {nombre} ({cod})",
                ["inicio", "en_proceso", "alta"],
                index=["inicio", "en_proceso", "alta"].index(estado_actual),
                key=f"estado_{cod}"
            )
            if st.button("💾 Guardar", key=f"guardar_estado_{cod}"):
                data["estados"][cod] = nuevo_estado
                guardar_datos(data)
                st.success("✅ Estado actualizado")
                st.rerun()
            if cod in data["tareas"]:
                total = len(data["tareas"][cod])
                completadas = sum(1 for t in data["tareas"][cod] if t["completada"])
                st.caption(f"Tareas: {completadas}/{total} completadas")
            st.divider()

    elif pagina == "tutor" and st.session_state.rol == "estudiante":
        st.subheader("📋 Mis solicitudes")
        mis_solicitudes = [s for s in data["solicitudes"] if s["estudiante_codigo"] == st.session_state.codigo]
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
