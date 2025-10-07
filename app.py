# app.py
import streamlit as st
import json, os, uuid, unicodedata
from datetime import datetime, date, time, timedelta

# ---------------------------
# Configuración página
# ---------------------------
st.set_page_config(page_title="Acompáñame - UPC", layout="centered", page_icon="🎓")

DATA_FILE = "datos.json"

# ---------------------------
# Utilidades
# ---------------------------
def normalize(text):
    """Normaliza texto: quita tildes, pasa a minúsculas y recorta."""
    if text is None:
        return ""
    text = str(text).strip().lower()
    nfkd = unicodedata.normalize('NFKD', text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])

def generar_id(prefix="id"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

# ---------------------------
# Cargar / Guardar datos (robusto)
# ---------------------------
def cargar_datos():
    if not os.path.exists(DATA_FILE):
        data = {
            "solicitudes": [],
            "mensajes": {},
            "tareas": {},
            "estados": {},
            "events": {},
            "estudiantes": {},
            "config": {},
            "recompensas": {}  # NUEVO: sistema de recompensas
        }
        default_est = {
            "UPC2025-001": {"nombre": "María García", "tutor_id": "tutor_juan", "activo": True, "permitir_crear_tareas": False},
            "UPC2025-002": {"nombre": "Carlos Méndez", "tutor_id": "tutor_ana", "activo": True, "permitir_crear_tareas": False},
            "UPC2025-003": {"nombre": "Lucía Rojas", "tutor_id": "tutor_juan", "activo": True, "permitir_crear_tareas": False},
        }
        data["estudiantes"].update(default_est)
        data["estados"] = {k: "inicio" for k in default_est.keys()}
        data["recompensas"] = {k: {"sesiones_enfoque": 0, "puntos": 0} for k in default_est.keys()}  # Inicializar recompensas
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # asegurar claves
    defaults = {
        "solicitudes": [], "mensajes": {}, "tareas": {}, "estados": {}, "events": {}, "estudiantes": {}, "config": {}, "recompensas": {}
    }
    for k, v in defaults.items():
        if k not in data:
            data[k] = v

    # asegurar estudiantes por defecto si faltan
    default_est = {
        "UPC2025-001": {"nombre": "María García", "tutor_id": "tutor_juan", "activo": True, "permitir_crear_tareas": False},
        "UPC2025-002": {"nombre": "Carlos Méndez", "tutor_id": "tutor_ana", "activo": True, "permitir_crear_tareas": False},
        "UPC2025-003": {"nombre": "Lucía Rojas", "tutor_id": "tutor_juan", "activo": True, "permitir_crear_tareas": False},
    }
    for k, v in default_est.items():
        if k not in data["estudiantes"]:
            data["estudiantes"][k] = v
            data["estados"][k] = "inicio"
        # Asegurar recompensas para cada estudiante
        if k not in data["recompensas"]:
            data["recompensas"][k] = {"sesiones_enfoque": 0, "puntos": 0}

    return data

def guardar_datos(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------
# Tutores estáticos
# ---------------------------
TUTORES = {
    "tutor_juan": {"nombre": "Juan Pérez"},
    "tutor_ana": {"nombre": "Ana López"},
}

# ---------------------------
# Session state inicial
# ---------------------------
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False
    st.session_state.rol = None
    st.session_state.nombre = ""
    st.session_state.codigo = ""
    st.session_state.id_tutor = None
    st.session_state.pagina = "inicio"
    st.session_state.mensaje_exito = ""
    st.session_state.pagina_focus = {}
    st.session_state.enfoque_activo = False
    st.session_state.tiempo_restante = 25 * 60
    st.session_state.sesion_iniciada = False

def mostrar_mensaje_exito():
    if st.session_state.get("mensaje_exito"):
        st.success(st.session_state.mensaje_exito)
        st.session_state.mensaje_exito = ""

# ---------------------------
# Estilos simples (opcionales)
# ---------------------------
st.markdown("""
<style>
    .stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Pantalla de login
# ---------------------------
if not st.session_state.usuario_autenticado:
    st.title("🎓 Acompáñame")
    st.markdown("Sistema de apoyo anti-procrastinación - UPC")
    opcion = st.radio("Selecciona tu rol", ["Estudiante", "Tutor"])
    data = cargar_datos()

    if opcion == "Estudiante":
        codigo = st.text_input("Código UPC (ej: UPC2025-001)")
        nombre = st.text_input("Nombre completo")
        if st.button("Ingresar"):
            code = codigo.strip().upper()
            estudiantes = data.get("estudiantes", {})
            if code in estudiantes and normalize(nombre) == normalize(estudiantes[code].get("nombre")):
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "estudiante",
                    "nombre": estudiantes[code].get("nombre"),
                    "codigo": code,
                    "id_tutor": estudiantes[code].get("tutor_id"),
                    "pagina": "inicio"
                })
                st.session_state.mensaje_exito = f"Bienvenido/a {st.session_state.nombre}"
                st.rerun()
            else:
                st.error("Código o nombre incorrecto. Verifica mayúsculas o el nombre exacto.")
                if code in estudiantes:
                    st.info(f"Nombre esperado para {code}: {estudiantes[code].get('nombre')}")
    else:
        codigo_tutor = st.text_input("Código de tutor (TUTOR-JUAN o TUTOR-ANA)")
        if st.button("Ingresar"):
            if codigo_tutor.strip().upper() == "TUTOR-JUAN":
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "tutor",
                    "nombre": "Juan Pérez",
                    "id_tutor": "tutor_juan",
                    "pagina": "inicio"
                })
                st.session_state.mensaje_exito = "Bienvenido Juan Pérez"
                st.rerun()
            elif codigo_tutor.strip().upper() == "TUTOR-ANA":
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "tutor",
                    "nombre": "Ana López",
                    "id_tutor": "tutor_ana",
                    "pagina": "inicio"
                })
                st.session_state.mensaje_exito = "Bienvenida Ana López"
                st.rerun()
            else:
                st.error("Código de tutor inválido. Usa TUTOR-JUAN o TUTOR-ANA.")

# ---------------------------
# App principal
# ---------------------------
else:
    data = cargar_datos()
    mostrar_mensaje_exito()

    # header y logout
    col1, col2 = st.columns([4,1])
    with col1:
        st.title(f"👋 {st.session_state.nombre}")
    with col2:
        if st.button("🚪 Salir"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")
    # Barra de navegación HORIZONTAL (6 columnas)
    nav_cols = st.columns(6)
    with nav_cols[0]:
        if st.button("🏠 Inicio", key="nav_inicio", use_container_width=True):
            st.session_state.pagina = "inicio"; st.rerun()
    with nav_cols[1]:
        if st.button("✅ Tareas", key="nav_tareas", use_container_width=True):
            st.session_state.pagina = "tareas"; st.rerun()
    with nav_cols[2]:
        if st.button("🎯 Enfoque", key="nav_enfoque", use_container_width=True):
            st.session_state.pagina = "enfoque"; st.rerun()
    with nav_cols[3]:
        if st.button("🆘 Asesoría", key="nav_asesoria", use_container_width=True):
            st.session_state.pagina = "asesoria"; st.rerun()
    with nav_cols[4]:
        if st.button("💬 Chat", key="nav_chat", use_container_width=True):
            st.session_state.pagina = "chat"; st.rerun()
    label_tutor = "👨‍🏫 Tutor" if st.session_state.rol=="estudiante" else "📊 Alumnos"
    with nav_cols[5]:
        if st.button(label_tutor, key="nav_tutor", use_container_width=True):
            st.session_state.pagina = "tutor"; st.rerun()

    # Actualizar página según botones de navegación
    if "nav_inicio" in st.session_state and st.session_state.nav_inicio:
        st.session_state.pagina = "inicio"
    elif "nav_tareas" in st.session_state and st.session_state.nav_tareas:
        st.session_state.pagina = "tareas"
    elif "nav_enfoque" in st.session_state and st.session_state.nav_enfoque:
        st.session_state.pagina = "enfoque"
    elif "nav_asesoria" in st.session_state and st.session_state.nav_asesoria:
        st.session_state.pagina = "asesoria"
    elif "nav_chat" in st.session_state and st.session_state.nav_chat:
        st.session_state.pagina = "chat"
    elif "nav_tutor" in st.session_state and st.session_state.nav_tutor:
        st.session_state.pagina = "tutor"
    
    pagina = st.session_state.pagina

    # ---------------------------
    # INICIO
    # ---------------------------
    if pagina == "inicio":
        st.subheader("🎓 Bienvenido/a a Acompáñame")
        st.info("Usa la barra horizontal para navegar. Las confirmaciones aparecerán en esta pantalla.")
        if st.session_state.rol == "estudiante":
            tareas = data.get("tareas", {}).get(st.session_state.codigo, [])
            total = len(tareas)
            completadas = sum(1 for t in tareas if t.get("completada"))
            porc = int((completadas/total)*100) if total else 0
            st.markdown(f"**Progreso de tareas:** {completadas}/{total} — {porc}%")
            st.progress(porc/100 if total else 0)
            
            # Mostrar progreso de recompensas
            sesiones = data["recompensas"][st.session_state.codigo]["sesiones_enfoque"]
            st.markdown(f"**Sesiones de enfoque:** {sesiones}/20")
            st.progress(min(sesiones / 20, 1.0))
            if sesiones >= 5:
                st.markdown("### 🎁 ¡Recompensas disponibles!")
                if sesiones >= 5:
                    st.markdown("• **Entrada de cine gratis**")
                if sesiones >= 10:
                    st.markdown("• **Almuerzo gratis en cafetería UPC**")
                if sesiones >= 15:
                    st.markdown("• **Liberación de tarea tipo**")
                if sesiones >= 20:
                    st.markdown("• **Reconocimiento institucional**")

        # Mostrar próximos eventos del usuario
        eventos_usuario = []
        for ev in data.get("events", {}).values():
            if st.session_state.rol == "estudiante" and ev.get("estudiante_codigo") == st.session_state.codigo:
                eventos_usuario.append(ev)
            if st.session_state.rol == "tutor" and ev.get("tutor_id") == st.session_state.id_tutor:
                eventos_usuario.append(ev)
        if eventos_usuario:
            st.markdown("### 📆 Próximas sesiones")
            for ev in sorted(eventos_usuario, key=lambda x: x.get("fecha")+x.get("hora")):
                st.markdown(f"- **{ev.get('title')}** | {ev.get('fecha')} {ev.get('hora')} — {ev.get('descripcion','')}")
        else:
            st.info("No hay sesiones agendadas.")

    # ---------------------------
    # TAREAS
    # ---------------------------
    elif pagina == "tareas":
        st.subheader("📌 Tareas")
        if st.session_state.rol == "estudiante":
            codigo_usuario = st.session_state.codigo
        else:
            alumnos = [k for k,v in data.get("estudiantes", {}).items() if v.get("tutor_id")==st.session_state.id_tutor]
            sel = st.selectbox("Selecciona alumno", ["---"] + alumnos, key="sel_alumno_tutor")
            codigo_usuario = None if sel=="---" else sel

        if codigo_usuario:
            tareas_usuario = data.get("tareas", {}).get(codigo_usuario, [])
            if tareas_usuario:
                st.markdown("### Tareas asignadas")
                for t in tareas_usuario:
                    colA, colB = st.columns([4,1])
                    with colA:
                        st.write(f"**{t['nombre']}** — 📅 {t.get('fecha_limite','')}")
                    with colB:
                        if not t.get("completada"):
                            if st.button("✅ Completar", key=f"comp_{codigo_usuario}_{t['id']}"):
                                t["completada"] = True
                                data["tareas"][codigo_usuario] = tareas_usuario
                                guardar_datos(data)
                                st.session_state.mensaje_exito = "Tarea marcada como completada"
                                st.rerun()
                        else:
                            st.write("✔️")
            else:
                st.info("No hay tareas asignadas.")

            permitir = data["estudiantes"].get(codigo_usuario, {}).get("permitir_crear_tareas", False)
            if st.session_state.rol == "estudiante" and not permitir:
                st.caption("Tu tutor administra tus tareas. Solicita permiso si quieres crear tareas.")
            else:
                with st.form("añadir_tarea"):
                    nombre_t = st.text_input("Nombre de la tarea")
                    fecha_lim = st.date_input("Fecha límite", value=date.today())
                    if st.form_submit_button("➕ Añadir tarea"):
                        tareas_lista = data.get("tareas", {}).get(codigo_usuario, [])
                        tarea = {"id": len(tareas_lista)+1, "nombre": nombre_t, "fecha_limite": str(fecha_lim), "completada": False}
                        tareas_lista.append(tarea)
                        data["tareas"][codigo_usuario] = tareas_lista
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "✅ Tarea añadida"
                        st.rerun()
        else:
            st.info("Selecciona un alumno (si eres tutor) o inicia sesión como estudiante.")

    # ---------------------------
    # MODO ENFOQUE
    # ---------------------------
    elif pagina == "enfoque":
        st.subheader("🎯 Modo Enfoque")
        
        if not st.session_state.enfoque_activo:
            st.info("Activa el modo enfoque para ganar puntos y recompensas institucionales")
            col1, col2 = st.columns(2)
            with col1:
                duracion = st.selectbox("Duración", ["25 min", "50 min"], key="duracion_enfoque")
            with col2:
                if st.button("🚀 Iniciar sesión de enfoque"):
                    st.session_state.enfoque_activo = True
                    st.session_state.tiempo_restante = 25 * 60 if duracion == "25 min" else 50 * 60
                    st.session_state.sesion_iniciada = True
                    st.rerun()
        else:
            # Mostrar temporizador
            mins, secs = divmod(st.session_state.tiempo_restante, 60)
            st.markdown(f"<h1 style='text-align: center; color: #C8102E;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
            
            st.warning("¡No abandones esta página! Estás en modo enfoque.")
            
            if st.session_state.tiempo_restante > 0 and st.session_state.sesion_iniciada:
                import time
                time.sleep(1)
                st.session_state.tiempo_restante -= 1
                st.rerun()
            else:
                st.session_state.enfoque_activo = False
                st.session_state.sesion_iniciada = False
                
                # Registrar sesión completada
                if st.session_state.rol == "estudiante":
                    data["recompensas"][st.session_state.codigo]["sesiones_enfoque"] += 1
                    data["recompensas"][st.session_state.codigo]["puntos"] += 10
                    guardar_datos(data)
                
                st.balloons()
                st.success("🎉 ¡Excelente! Has completado una sesión de enfoque.")
                st.info("Acumulas puntos para recompensas institucionales.")
                
                if st.button("Volver al inicio"):
                    st.session_state.pagina = "inicio"
                    st.rerun()

    # ---------------------------
    # RECURSOS ANTI-DISTRACCIÓN
    # ---------------------------
    elif pagina == "recursos":
        st.subheader("🛡️ Herramientas para evitar distracciones")
        
        st.markdown("### 📱 Aplicaciones recomendadas")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### **Celular**")
            st.markdown("- **iOS**: [Tiempo de uso](https://support.apple.com/es-es/102660)")
            st.markdown("- **Android**: [Bienestar digital](https://wellbeing.google.com/)")
        with col2:
            st.markdown("#### **Computadora**")
            st.markdown("- **Windows/Mac**: [Cold Turkey](https://getcoldturkey.com/)")
            st.markdown("- **Chrome**: [StayFocusd](https://stayfocusd.com/)")
        
        st.markdown("### 🧠 Técnicas de autorregulación")
        st.markdown("""
        1. **Teléfono en modo avión** durante sesiones de estudio
        2. **Estudia en espacios públicos** (biblioteca, cafetería)
        3. **Compromiso público**: comparte tus metas con tu tutor
        """)
        
        st.markdown("### 🎁 Sistema de recompensas UPC")
        st.markdown("""
        - **5 sesiones** = Entrada de cine gratis
        - **10 sesiones** = Almuerzo gratis en cafetería UPC  
        - **15 sesiones** = Liberación de una tarea tipo en tus cursos
        - **20 sesiones** = Reconocimiento en ceremonia de innovación
        """)
        
        # Mostrar progreso del estudiante
        if st.session_state.rol == "estudiante":
            sesiones = data["recompensas"][st.session_state.codigo]["sesiones_enfoque"]
            st.progress(min(sesiones / 20, 1.0))
            st.caption(f"Sesiones completadas: {sesiones}/20")
            puntos = data["recompensas"][st.session_state.codigo]["puntos"]
            st.caption(f"Puntos acumulados: {puntos}")

    # ---------------------------
    # ASESORIA - estudiante
    # ---------------------------
    elif pagina == "asesoria" and st.session_state.rol == "estudiante":
        st.subheader("🆘 Solicitar asesoría")
        with st.form("solicitud_asesoria"):
            mensaje = st.text_area("Describe tu necesidad (máx 200 chars)", max_chars=200)
            if st.form_submit_button("📤 Enviar solicitud"):
                if not mensaje:
                    st.error("Describe tu necesidad")
                else:
                    sol_id = generar_id("sol")
                    nueva = {
                        "id": sol_id,
                        "estudiante": st.session_state.nombre,
                        "estudiante_codigo": st.session_state.codigo,
                        "tutor_id": st.session_state.id_tutor,
                        "mensaje": mensaje,
                        "fecha_envio": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "fecha_aceptacion": None,
                        "estado": "pendiente"
                    }
                    data["solicitudes"].append(nueva)
                    guardar_datos(data)
                    st.session_state.mensaje_exito = "✅ Solicitud enviada. Espera la confirmación de tu tutor."
                    st.rerun()

        st.markdown("### Mis solicitudes")
        mis = [s for s in data.get("solicitudes", []) if s["estudiante_codigo"]==st.session_state.codigo]
        if mis:
            for s in sorted(mis, key=lambda x: x["fecha_envio"], reverse=True):
                estado_label = "✅ Aceptada" if s["estado"]=="en_chat" else ("⏳ Pendiente" if s["estado"]=="pendiente" else s["estado"])
                st.markdown(f"- {s['mensaje']} | {s['fecha_envio']} — **{estado_label}**")
        else:
            st.info("No has enviado solicitudes.")

    # ---------------------------
    # ASESORIA - tutor
    # ---------------------------
    elif pagina == "asesoria" and st.session_state.rol == "tutor":
        st.subheader("📬 Solicitudes pendientes")
        pendientes = [s for s in data.get("solicitudes", []) if s["tutor_id"]==st.session_state.id_tutor and s["estado"]=="pendiente"]
        if pendientes:
            for s in pendientes:
                st.markdown(f"**Estudiante:** {s['estudiante']} ({s['estudiante_codigo']})")
                st.markdown(f"**Mensaje:** {s['mensaje']}")
                c1, c2, c3 = st.columns([1,1,1])
                with c1:
                    if st.button("✅ Aceptar", key=f"acept_{s['id']}"):
                        s["estado"] = "en_chat"
                        s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        data["mensajes"][s["id"]] = []
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "✅ Solicitud aceptada. Usa el chat para comunicarte."
                        st.rerun()
                with c2:
                    if st.button("❌ Rechazar", key=f"rej_{s['id']}"):
                        s["estado"] = "rechazada"
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "Solicitud rechazada"
                        st.rerun()
                with c3:
                    if st.button("📅 Agendar", key=f"ag_{s['id']}"):
                        st.session_state.pagina = "chat"
                        st.session_state.pagina_focus = {"solicitud_id": s["id"], "open_schedule": True}
                        st.rerun()
                st.divider()
        else:
            st.info("No hay solicitudes pendientes.")

    # ---------------------------
    # CHAT (bidireccional) + agendado
    # ---------------------------
    elif pagina == "chat":
        if st.session_state.rol == "estudiante":
            chats = [s for s in data.get("solicitudes", []) if s["estudiante_codigo"]==st.session_state.codigo and s["estado"]=="en_chat"]
        else:
            chats = [s for s in data.get("solicitudes", []) if s["tutor_id"]==st.session_state.id_tutor and s["estado"]=="en_chat"]

        if chats:
            solicitud = chats[0]
            otro = TUTORES[solicitud["tutor_id"]]["nombre"] if st.session_state.rol=="estudiante" else solicitud["estudiante"]
            st.subheader(f"💬 Chat con {otro}")

            mensajes = data.get("mensajes", {}).get(solicitud["id"], [])
            for m in mensajes:
                st.text(f"{m['usuario']} ({m['fecha']}): {m['texto']}")

            with st.form(f"chat_form_{solicitud['id']}"):
                txt = st.text_input("Escribe un mensaje", placeholder="Puedes proponer fecha con: PROPONER YYYY-MM-DD HH:MM")
                if st.form_submit_button("Enviar") and txt:
                    mensajes.append({"usuario": st.session_state.nombre, "texto": txt, "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    data["mensajes"][solicitud["id"]] = mensajes
                    guardar_datos(data)
                    st.session_state.mensaje_exito = "✅ Mensaje enviado"
                    if txt.strip().upper().startswith("PROPONER"):
                        parts = txt.split()
                        if len(parts) >= 3:
                            fecha_str = parts[1]
                            hora_str = parts[2]
                            st.session_state.pagina_focus = {"solicitud_id": solicitud["id"], "open_schedule": True, "pref_fecha": fecha_str, "pref_hora": hora_str}
                    st.rerun()

            st.markdown("---")
            # Agendado
            focus = st.session_state.get("pagina_focus", {}) or {}
            open_schedule = focus.get("open_schedule", False)
            pref_fecha = focus.get("pref_fecha")
            pref_hora = focus.get("pref_hora")

            if st.checkbox("📅 Agendar / Proponer sesión", value=open_schedule):
                with st.form(f"form_agenda_{solicitud['id']}"):
                    title = st.text_input("Título", value="Sesión de asesoría")
                    descripcion = st.text_area("Descripción (opcional)", value=solicitud.get("mensaje",""))
                    fecha_sel = st.date_input("Fecha", value=(datetime.strptime(pref_fecha, "%Y-%m-%d").date() if pref_fecha else date.today()))
                    hora_input = st.time_input("Hora", value=(datetime.strptime(pref_hora,"%H:%M").time() if pref_hora else time(hour=15)))
                    dur = st.number_input("Duración (minutos)", min_value=15, max_value=180, value=60)
                    reminder = st.number_input("Recordatorio (minutos antes)", min_value=1, max_value=1440, value=30)
                    if st.form_submit_button("📌 Agendar sesión"):
                        event_id = generar_id("evt")
                        ev = {
                            "id": event_id,
                            "title": title,
                            "descripcion": descripcion,
                            "fecha": fecha_sel.strftime("%Y-%m-%d"),
                            "hora": hora_input.strftime("%H:%M"),
                            "duration_minutes": int(dur),
                            "recordatorio_minutos": int(reminder),
                            "solicitud_id": solicitud["id"],
                            "estudiante_codigo": solicitud["estudiante_codigo"],
                            "tutor_id": solicitud["tutor_id"],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        data["events"][event_id] = ev
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "✅ Sesión agendada. Descarga el .ics si deseas añadirla a tu calendario."
                        st.session_state.pagina_focus = {}
                        st.rerun()

            # Mostrar eventos vinculados
            eventos_rel = [ev for ev in data.get("events", {}).values() if ev.get("solicitud_id")==solicitud["id"]]
            if eventos_rel:
                st.markdown("### Eventos vinculados")
                for ev in eventos_rel:
                    st.markdown(f"- **{ev['title']}** — {ev['fecha']} {ev['hora']} ({ev['duration_minutes']} min)")
                    # generar ICS simple
                    def crear_ics(ev):
                        try:
                            date_part = ev["fecha"].replace("-", "")
                            time_part = ev["hora"].replace(":", "")
                            dtstart = f"{date_part}T{time_part}00"
                            dtstart_obj = datetime.strptime(ev["fecha"] + " " + ev["hora"], "%Y-%m-%d %H:%M")
                            dtend_obj = dtstart_obj + timedelta(minutes=ev.get("duration_minutes", 60))
                            dtend = dtend_obj.strftime("%Y%m%dT%H%M00")
                            uid = ev.get("id", generar_id("evt"))
                            reminder = ev.get("recordatorio_minutos", 30)
                            alarm_trigger = f"-PT{reminder}M"
                            ics = (
f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Acompaname UPC//EN\nBEGIN:VEVENT\nUID:{uid}\nDTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M00')}\nDTSTART:{dtstart}\nDTEND:{dtend}\nSUMMARY:{ev.get('title')}\nDESCRIPTION:{ev.get('descripcion','')}\nEND:VEVENT\nBEGIN:VALARM\nTRIGGER:{alarm_trigger}\nACTION:DISPLAY\nDESCRIPTION:Recordatorio - {ev.get('title')}\nEND:VALARM\nEND:VCALENDAR"
                            )
                            return ics
                        except:
                            return None
                    ics = crear_ics(ev)
                    if ics:
                        st.download_button(label="Descargar .ics", data=ics, file_name=f"evento_{ev['id']}.ics", mime="text/calendar")
        else:
            st.info("No tienes conversaciones activas.")

    # ---------------------------
    # PANEL TUTOR
    # ---------------------------
    elif pagina == "tutor" and st.session_state.rol == "tutor":
        st.subheader("📊 Panel del tutor")
        estudiantes = data.get("estudiantes", {})
        mis_alumnos = {cod:info for cod,info in estudiantes.items() if info.get("tutor_id")==st.session_state.id_tutor}
        st.markdown("### Mis alumnos")
        if mis_alumnos:
            for cod, info in mis_alumnos.items():
                tareas = data.get("tareas", {}).get(cod, [])
                completadas = sum(1 for t in tareas if t.get("completada"))
                total = len(tareas)
                porc = int((completadas/total)*100) if total else 0
                st.markdown(f"**{info['nombre']}** ({cod}) — {completadas}/{total} tareas — {porc}%")
                c1, c2, c3 = st.columns([1,1,1])
                with c1:
                    if st.button("Permitir tareas", key=f"perm_{cod}"):
                        data["estudiantes"][cod]["permitir_crear_tareas"] = True
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"Permiso activado para {info['nombre']}"
                        st.rerun()
                with c2:
                    if st.button("Deshabilitar", key=f"nperm_{cod}"):
                        data["estudiantes"][cod]["permitir_crear_tareas"] = False
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"Permiso desactivado para {info['nombre']}"
                        st.rerun()
                with c3:
                    if st.button("Dar de alta", key=f"alta_{cod}"):
                        data["estados"][cod] = "alta"
                        data["estudiantes"][cod]["activo"] = False
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"{info['nombre']} marcado como alta"
                        st.rerun()
                st.divider()
        else:
            st.info("No tienes alumnos asignados.")

        st.markdown("---")
        st.markdown("### ➕ Asignar tarea a alumno")
        with st.form("asignar_tarea_tutor"):
            alumnos_op = list(mis_alumnos.keys())
            sel_al = st.selectbox("Selecciona alumno", ["---"] + alumnos_op)
            nombre_t = st.text_input("Nombre de la tarea")
            fecha_lim_t = st.date_input("Fecha límite", value=date.today())
            if st.form_submit_button("Asignar tarea"):
                if sel_al == "---" or not nombre_t:
                    st.error("Selecciona alumno y escribe nombre de la tarea")
                else:
                    tareas_al = data.get("tareas", {}).get(sel_al, [])
                    tarea = {"id": len(tareas_al)+1, "nombre": nombre_t, "fecha_limite": str(fecha_lim_t), "completada": False}
                    tareas_al.append(tarea)
                    data["tareas"][sel_al] = tareas_al
                    guardar_datos(data)
                    st.session_state.mensaje_exito = f"Tarea asignada a {data['estudiantes'][sel_al]['nombre']}"
                    st.rerun()

        st.markdown("---")
        st.markdown("### 👩‍🎓 Inscribir nuevo alumno")
        with st.form("inscribir_alumno"):
            nuevo_codigo = st.text_input("Código (ej: UPC2025-004)")
            nuevo_nombre = st.text_input("Nombre completo")
            permitir_crear = st.checkbox("Permitir crear tareas", value=False)
            if st.form_submit_button("Inscribir alumno"):
                codeu = nuevo_codigo.strip().upper()
                if not codeu or not nuevo_nombre:
                    st.error("Completa código y nombre")
                elif codeu in data["estudiantes"]:
                    st.error("El código ya existe")
                else:
                    data["estudiantes"][codeu] = {"nombre": nuevo_nombre, "tutor_id": st.session_state.id_tutor, "activo": True, "permitir_crear_tareas": permitir_crear}
                    data["estados"][codeu] = "inicio"
                    data["recompensas"][codeu] = {"sesiones_enfoque": 0, "puntos": 0}  # Inicializar recompensas
                    guardar_datos(data)
                    st.session_state.mensaje_exito = f"Alumno {nuevo_nombre} inscrito correctamente"
                    st.rerun()

    # ---------------------------
    # Si estudiante visita 'tutor' (mis solicitudes)
    # ---------------------------
    elif pagina == "tutor" and st.session_state.rol == "estudiante":
        st.subheader("📋 Mis solicitudes")
        mis = [s for s in data.get("solicitudes", []) if s["estudiante_codigo"]==st.session_state.codigo]
        if mis:
            for s in mis:
                status = "✅ Aceptada" if s["estado"]=="en_chat" else ("⏳ Pendiente" if s["estado"]=="pendiente" else s["estado"])
                st.markdown(f"- {s['mensaje']} | {s['fecha_envio']} — **{status}**")
        else:
            st.info("No has enviado solicitudes.")