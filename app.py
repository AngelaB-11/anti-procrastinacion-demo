# app.py
import streamlit as st
import json, os, uuid
from datetime import datetime, date, time

# ---------------------------
# Config y estilos
# ---------------------------
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
        padding: 8px 14px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #a00d25;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Archivo JSON compartido
# ---------------------------
DATA_FILE = "datos.json"

def cargar_datos():
    if not os.path.exists(DATA_FILE):
        data_inicial = {
            "solicitudes": [],        # lista de dicts
            "mensajes": {},          # key: solicitud_id (str) -> list msgs
            "tareas": {},            # key: usuario_code -> list tareas
            "estados": {},           # key: estudiante_code -> estado
            "events": {},            # key: event_id -> event dict
            "estudiantes": {},       # persistir estudiantes (editable por tutor)
            "config": {}             # opciones globales si se necesitan
        }
        # cargar estudiantes por defecto
        default_est = {
            "UPC2025-001": {"nombre": "María García", "tutor_id": "tutor_juan", "activo": True, "permitir_crear_tareas": False},
            "UPC2025-002": {"nombre": "Carlos Méndez", "tutor_id": "tutor_ana", "activo": True, "permitir_crear_tareas": False},
            "UPC2025-003": {"nombre": "Lucía Rojas", "tutor_id": "tutor_juan", "activo": True, "permitir_crear_tareas": False},
        }
        data_inicial["estudiantes"] = default_est
        data_inicial["estados"] = {k: "inicio" for k in default_est.keys()}
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data_inicial, f, ensure_ascii=False, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_datos(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------
# Datos estaticos (tutores)
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

# Mostrar mensaje de exito guardado (si existe)
def mostrar_mensaje_exito():
    if st.session_state.get("mensaje_exito"):
        st.success(st.session_state.mensaje_exito)
        # Lo dejamos visible hasta que el usuario navegue; no lo borramos inmediatamente
        st.session_state.mensaje_exito = ""

# ---------------------------
# Funciones utilitarias
# ---------------------------
def generar_id(prefix="id"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def crear_ics(event):
    """
    Genera contenido iCalendar (.ics) para evento con alarma.
    event dict fields: title, descripcion, fecha (YYYY-MM-DD), hora (HH:MM), duration_minutes, reminder_minutes
    """
    # build datetime strings: YYYYMMDDTHHMM00
    try:
        date_part = event["fecha"].replace("-", "")
        time_part = event["hora"].replace(":", "")
        dtstart = f"{date_part}T{time_part}00"
        # end time
        # simple addition of minutes:
        hh, mm = map(int, event["hora"].split(":"))
        from datetime import timedelta, datetime as dt
        dtstart_obj = dt.strptime(event["fecha"] + " " + event["hora"], "%Y-%m-%d %H:%M")
        dtend_obj = dtstart_obj + timedelta(minutes=event.get("duration_minutes", 60))
        dtend = dtend_obj.strftime("%Y%m%dT%H%M00")
        uid = event.get("id", generar_id("evt"))
        # alarm
        reminder = event.get("recordatorio_minutos", 30)
        alarm_trigger = f"-PT{reminder}M"
        ics = (
f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Acompaname UPC//EN\nBEGIN:VEVENT\nUID:{uid}\nDTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M00')}\nDTSTART:{dtstart}\nDTEND:{dtend}\nSUMMARY:{event.get('title')}\nDESCRIPTION:{event.get('descripcion','')}\nEND:VEVENT\nBEGIN:VALARM\nTRIGGER:{alarm_trigger}\nACTION:DISPLAY\nDESCRIPTION:Recordatorio - {event.get('title')}\nEND:VALARM\nEND:VCALENDAR"
        )
        return ics
    except Exception as e:
        return None

def calcular_progreso(tareas):
    total = len(tareas)
    if total == 0:
        return 0, 0
    completadas = sum(1 for t in tareas if t.get("completada"))
    porcentaje = int((completadas / total) * 100)
    return porcentaje, completadas

def etiqueta_motivacional(porc):
    if porc == 0:
        return "¡Comienza ahora! 💪"
    if 1 <= porc <= 24:
        return "¡Ánimo, un paso a la vez! 😊"
    if 25 <= porc <= 49:
        return "¡Buen avance! 🙂"
    if 50 <= porc <= 79:
        return "¡Vas muy bien! 🔥"
    if 80 <= porc <= 99:
        return "¡Casi listo! 🏁"
    return "¡Objetivo cumplido! 🎉"

# ---------------------------
# Página de login
# ---------------------------
if not st.session_state.usuario_autenticado:
    st.title("🎓 Acompáñame")
    st.markdown("Sistema de apoyo anti-procrastinación - UPC")

    opcion = st.radio("Selecciona tu rol", ["Estudiante", "Tutor"])

    if opcion == "Estudiante":
        codigo = st.text_input("Código UPC (ej: UPC2025-001)")
        nombre = st.text_input("Nombre completo")
        if st.button("Ingresar"):
            data = cargar_datos()
            estudiantes = data.get("estudiantes", {})
            if codigo in estudiantes and estudiantes[codigo]["nombre"].lower() == nombre.lower():
                st.session_state.update({
                    "usuario_autenticado": True,
                    "rol": "estudiante",
                    "nombre": nombre,
                    "codigo": codigo,
                    "id_tutor": estudiantes[codigo]["tutor_id"],
                    "pagina": "inicio"
                })
                st.session_state.mensaje_exito = f"Bienvenido/a {nombre}"
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
                st.session_state.mensaje_exito = "Bienvenido Juan Pérez"
                st.rerun()
            elif codigo_tutor == "TUTOR-ANA":
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
                st.error("Código inválido")

# ---------------------------
# App principal (autenticado)
# ---------------------------
else:
    # Cargar datos comunes
    data = cargar_datos()
    mostrar_mensaje_exito()

    # Header y logout
    col1, col2 = st.columns([4,1])
    with col1:
        st.title(f"👋 {st.session_state.nombre}")
    with col2:
        if st.button("🚪 Salir"):
            # limpiar session state pero guardar mensaje si se desea
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")
    nav_cols = st.columns(5)
    with nav_cols[0]: st.button("🏠 Inicio", key="inicio", use_container_width=True)
    with nav_cols[1]: st.button("✅ Tareas", key="tareas", use_container_width=True)
    with nav_cols[2]: st.button("🆘 Asesoría", key="asesoria", use_container_width=True)
    with nav_cols[3]: st.button("💬 Chat", key="chat", use_container_width=True)
    label_tutor = "👨‍🏫 Tutor" if st.session_state.rol=="estudiante" else "📊 Alumnos"
    with nav_cols[4]: st.button(label_tutor, key="tutor", use_container_width=True)

    # Determinar página activa
    for p in ["inicio","tareas","asesoria","chat","tutor"]:
        if p in st.session_state and st.session_state[p]:
            st.session_state.pagina = p

    pagina = st.session_state.pagina

    # ---------------------------
    # INICIO
    # ---------------------------
    if pagina == "inicio":
        st.subheader("🎓 Bienvenido/a a Acompáñame")
        st.info("Usa la barra inferior para navegar. Tus acciones mostrarán mensajes de confirmación aquí.")
        # Mostrar próximos eventos del usuario
        eventos_usuario = []
        # buscar eventos donde participante incluye usuario (estudiante) o tutor_id
        for eid, ev in data.get("events", {}).items():
            if st.session_state.rol == "estudiante" and ev.get("estudiante_codigo") == st.session_state.codigo:
                eventos_usuario.append(ev)
            if st.session_state.rol == "tutor" and ev.get("tutor_id") == st.session_state.id_tutor:
                eventos_usuario.append(ev)
        if eventos_usuario:
            st.markdown("### 📆 Próximas sesiones agendadas")
            for ev in sorted(eventos_usuario, key=lambda x: x.get("fecha")+" "+x.get("hora")):
                st.markdown(f"- **{ev.get('title')}** | {ev.get('fecha')} {ev.get('hora')} ({ev.get('descripcion','')})")
                # permitir descargar ics
                ics = crear_ics(ev)
                if ics:
                    st.download_button(label="Descargar .ics", data=ics, file_name=f"evento_{ev.get('id')}.ics", mime="text/calendar")
        else:
            st.info("No hay sesiones agendadas.")

        # Mostrar progreso rapido si es estudiante
        if st.session_state.rol == "estudiante":
            tareas_usuario = data.get("tareas", {}).get(st.session_state.codigo, [])
            porc, comp = calcular_progreso(tareas_usuario)
            st.markdown("### 📈 Progreso de tareas")
            st.progress(porc / 100 if porc else 0)
            st.write(f"{comp}/{len(tareas_usuario)} completadas — {porc}%")
            st.write(etiqueta_motivacional(porc))

        # Links rapidos
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Mis tareas", use_container_width=True):
                st.session_state.pagina = "tareas"; st.rerun()
        with col2:
            if st.button("🆘 Solicitar asesoría", use_container_width=True):
                st.session_state.pagina = "asesoria"; st.rerun()

    # ---------------------------
    # TAREAS
    # ---------------------------
    elif pagina == "tareas":
        st.subheader("📌 Tareas")
        # codigo de guardado: por estudiante; para tutor podemos mostrar por alumno
        if st.session_state.rol == "estudiante":
            codigo_usuario = st.session_state.codigo
        else:
            # tutor: seleccionar alumno
            alumnos = [k for k,v in data.get("estudiantes", {}).items() if v.get("tutor_id") == st.session_state.id_tutor]
            sel = st.selectbox("Selecciona alumno", ["---"] + alumnos, key="sel_alumno_tutor")
            if sel and sel != "---":
                codigo_usuario = sel
            else:
                codigo_usuario = None

        # si hay alumno seleccionado o es estudiante
        if codigo_usuario:
            tareas_usuario = data["tareas"].get(codigo_usuario, [])
            # mostrar progreso
            porc, comp = calcular_progreso(tareas_usuario)
            st.markdown(f"**Progreso:** {comp}/{len(tareas_usuario)} — {porc}%")
            st.progress(porc/100 if porc else 0)
            st.write(etiqueta_motivacional(porc))

            # Mostrar tareas
            if tareas_usuario:
                st.markdown("### Tareas")
                for t in tareas_usuario:
                    col1, col2 = st.columns([5,1])
                    with col1:
                        st.write(f"**{t['nombre']}** — 📅 {t['fecha_limite']}")
                        if t.get("descripcion"):
                            st.caption(t["descripcion"])
                    with col2:
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

            # Si el estudiante tiene permiso, puede añadir tarea (configurable por tutor)
            permitir = data["estudiantes"].get(codigo_usuario, {}).get("permitir_crear_tareas", False)
            if st.session_state.rol == "estudiante" and not permitir:
                st.caption("Tu tutor administra tus tareas. Si consideras que deberías crear tus propias tareas, solicita permiso a tu tutor.")
            else:
                with st.form("añadir_tarea"):
                    nombre_tarea = st.text_input("Nombre de la tarea")
                    descripcion = st.text_area("Descripción (opcional)")
                    fecha_limite = st.date_input("Fecha límite", value=date.today())
                    submit = st.form_submit_button("➕ Añadir tarea")
                    if submit and nombre_tarea:
                        tarea = {
                            "id": len(tareas_usuario)+1,
                            "nombre": nombre_tarea,
                            "descripcion": descripcion,
                            "fecha_limite": str(fecha_limite),
                            "completada": False
                        }
                        tareas_usuario.append(tarea)
                        data["tareas"][codigo_usuario] = tareas_usuario
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "✅ Tarea añadida"
                        st.rerun()

        else:
            st.info("Selecciona un alumno para ver/administrar sus tareas.")

    # ---------------------------
    # ASESORIA - estudiante solicita
    # ---------------------------
    elif pagina == "asesoria" and st.session_state.rol == "estudiante":
        st.subheader("🆘 Solicitar asesoría")
        tutor_info = data["estudiantes"].get(st.session_state.codigo)  # por si actualizado
        tutor_nombre = TUTORES.get(st.session_state.id_tutor, {}).get("nombre", "Tu tutor")
        st.info(f"Tutor asignado: **{tutor_nombre}**")

        with st.form("solicitud_asesoria"):
            mensaje = st.text_area("Describe tu necesidad/tema (máx 200 chars)", max_chars=200)
            submit = st.form_submit_button("📤 Enviar solicitud")
            if submit:
                if not mensaje:
                    st.error("Describe brevemente tu necesidad")
                else:
                    nueva_id = generar_id("sol")
                    nueva_solicitud = {
                        "id": nueva_id,
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
                    st.session_state.mensaje_exito = "✅ Solicitud enviada. Espera a que tu tutor la acepte."
                    st.rerun()

        # listar mis solicitudes en el mismo lugar
        mis_solicitudes = [s for s in data["solicitudes"] if s["estudiante_codigo"] == st.session_state.codigo]
        if mis_solicitudes:
            st.markdown("### Mis solicitudes")
            for s in sorted(mis_solicitudes, key=lambda x: x["fecha_envio"], reverse=True):
                estado_label = "✅ Aceptada" if s["estado"] == "en_chat" else "⏳ Pendiente"
                st.markdown(f"- {s['mensaje']} — {s['fecha_envio']} | **{estado_label}**")
                if s.get("fecha_aceptacion"):
                    st.caption(f"Aceptada: {s['fecha_aceptacion']}")

    # ---------------------------
    # ASESORIA - tutor ve y acepta
    # ---------------------------
    elif pagina == "asesoria" and st.session_state.rol == "tutor":
        st.subheader("📬 Solicitudes pendientes")
        pendientes = [s for s in data.get("solicitudes", []) if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "pendiente"]
        if pendientes:
            for s in pendientes:
                st.markdown(f"**Estudiante:** {s['estudiante']} ({s['estudiante_codigo']})")
                st.markdown(f"**Mensaje:** {s['mensaje']}")
                cols = st.columns([1,1,1])
                with cols[0]:
                    if st.button("✅ Aceptar", key=f"aceptar_{s['id']}"):
                        s["estado"] = "en_chat"
                        s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        data["mensajes"][s["id"]] = []
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "✅ Solicitud aceptada. Puedes chatear y agendar la sesión."
                        st.rerun()
                with cols[1]:
                    if st.button("❌ Rechazar", key=f"rechazar_{s['id']}"):
                        s["estado"] = "rechazada"
                        guardar_datos(data)
                        st.session_state.mensaje_exito = "Solicitud rechazada"
                        st.rerun()
                with cols[2]:
                    if st.button("📅 Agendar ahora", key=f"agendar_{s['id']}"):
                        # crear evento inmediato en eventos vacios -> abrir formulario de agenda simple
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
        # seleccionar chat activo para rol
        if st.session_state.rol == "estudiante":
            chats = [s for s in data.get("solicitudes", []) if s["estudiante_codigo"] == st.session_state.codigo and s["estado"] == "en_chat"]
        else:
            chats = [s for s in data.get("solicitudes", []) if s["tutor_id"] == st.session_state.id_tutor and s["estado"] == "en_chat"]

        if chats:
            solicitud = chats[0]
            st.subheader(f"💬 Chat — {solicitud['estudiante']}") if st.session_state.rol == "tutor" else st.subheader(f"💬 Chat con Tutor")
            mensajes = data.get("mensajes", {}).get(solicitud["id"], [])

            # mostrar mensajes históricos
            for msg in mensajes:
                st.text(f"{msg['usuario']} ({msg['fecha']}): {msg['texto']}")

            # Chat send form
            with st.form(f"chat_form_{solicitud['id']}"):
                txt = st.text_input("Escribe un mensaje", placeholder="Proponer fecha: escribe 'PROPONER 2025-10-04 15:00' para agendar")
                submit = st.form_submit_button("Enviar")
                if submit and txt:
                    mensaje_obj = {
                        "usuario": st.session_state.nombre,
                        "texto": txt,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    mensajes.append(mensaje_obj)
                    data["mensajes"][solicitud["id"]] = mensajes
                    guardar_datos(data)
                    st.session_state.mensaje_exito = "✅ Mensaje enviado"
                    # check quick syntax: "PROPONER YYYY-MM-DD HH:MM" to auto-abrir agenda
                    if txt.strip().upper().startswith("PROPONER"):
                        # parse
                        parts = txt.split()
                        try:
                            fecha_str = parts[1]
                            hora_str = parts[2]
                            # abrir panel de agendado con valores precargados
                            st.session_state.pagina = "chat"
                            st.session_state.pagina_focus = {"solicitud_id": solicitud["id"], "pref_fecha": fecha_str, "pref_hora": hora_str, "open_schedule": True}
                        except:
                            pass
                    st.rerun()

            st.markdown("---")
            # PANEL DE AGENDADO DENTRO DEL CHAT
            focus = st.session_state.get("pagina_focus", {})
            open_schedule = False
            pref_fecha = None
            pref_hora = None
            if focus and focus.get("solicitud_id") == solicitud["id"]:
                open_schedule = focus.get("open_schedule", False)
                pref_fecha = focus.get("pref_fecha")
                pref_hora = focus.get("pref_hora")

            if st.checkbox("📅 Agendar / Proponer sesión", value=open_schedule):
                with st.form(f"form_agenda_{solicitud['id']}"):
                    title = st.text_input("Título", value="Sesión de asesoría")
                    descripcion = st.text_area("Descripción (opcional)", value=solicitud.get("mensaje", ""))
                    fecha_sel = st.date_input("Fecha", value = datetime.strptime(pref_fecha, "%Y-%m-%d").date() if pref_fecha else date.today())
                    hora_input = st.time_input("Hora", value = datetime.strptime(pref_hora, "%H:%M").time() if pref_hora else time(hour=15, minute=0))
                    dur = st.number_input("Duración (minutos)", min_value=15, max_value=180, value=60)
                    reminder = st.number_input("Recordatorio (minutos antes)", min_value=1, max_value=1440, value=30)
                    submit_ev = st.form_submit_button("📌 Agendar sesión")
                    if submit_ev:
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
                        st.session_state.mensaje_exito = "✅ Sesión agendada. Descarga el .ics para añadirla a tu calendario."
                        st.session_state.pagina_focus = {}  # limpiar
                        st.rerun()

            # mostrar opción de descargar ics para el evento si existe ya
            eventos_rel = [ev for ev in data.get("events", {}).values() if ev.get("solicitud_id") == solicitud["id"]]
            if eventos_rel:
                st.markdown("### Eventos vinculados")
                for ev in eventos_rel:
                    st.markdown(f"- **{ev['title']}** — {ev['fecha']} {ev['hora']} ({ev['duration_minutes']} min)")
                    ics = crear_ics(ev)
                    if ics:
                        st.download_button(label="Descargar .ics", data=ics, file_name=f"evento_{ev['id']}.ics", mime="text/calendar")

        else:
            st.info("No tienes conversaciones activas en chat.")

    # ---------------------------
    # PANEL TUTOR / GESTION ALUMNOS
    # ---------------------------
    elif pagina == "tutor" and st.session_state.rol == "tutor":
        st.subheader("📊 Panel del tutor")

        # 1) ver alumnos y progreso
        estudiantes = data.get("estudiantes", {})
        mis_alumnos = {cod:info for cod,info in estudiantes.items() if info.get("tutor_id") == st.session_state.id_tutor}
        st.markdown("### Mis alumnos")
        if mis_alumnos:
            for cod, info in mis_alumnos.items():
                tareas = data.get("tareas", {}).get(cod, [])
                porc, comp = calcular_progreso(tareas)
                cols = st.columns([3,1,1])
                with cols[0]:
                    st.markdown(f"**{info['nombre']}** ({cod}) - {info.get('activo','')}")
                    st.caption(f"Estado: {data.get('estados', {}).get(cod, 'inicio')}")
                with cols[1]:
                    st.write(f"{comp}/{len(tareas)}")
                with cols[2]:
                    st.progress(porc/100 if porc else 0)
                # opciones por alumno
                opts = st.columns([1,1,1])
                with opts[0]:
                    if st.button("🔁 Permitir tareas", key=f"perm_{cod}"):
                        data["estudiantes"][cod]["permitir_crear_tareas"] = True
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"El alumno {info['nombre']} puede crear tareas ahora."
                        st.rerun()
                with opts[1]:
                    if st.button("✖ Deshabilitar tareas", key=f"nperm_{cod}"):
                        data["estudiantes"][cod]["permitir_crear_tareas"] = False
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"El alumno {info['nombre']} ya no puede crear tareas."
                        st.rerun()
                with opts[2]:
                    if st.button("🎓 Dar de alta", key=f"alta_{cod}"):
                        data["estados"][cod] = "alta"
                        data["estudiantes"][cod]["activo"] = False
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"{info['nombre']} marcado como alta."
                        st.rerun()
                st.divider()
        else:
            st.info("No tienes alumnos asignados.")

        st.markdown("---")
        # 2) Asignar tarea a alumno(s)
        st.markdown("### ➕ Asignar tarea a alumno(s)")
        with st.form("asignar_tarea_tutor"):
            alumnos_op = list(mis_alumnos.keys())
            sel_alumno = st.selectbox("Selecciona alumno", ["---"] + alumnos_op)
            nombre_t = st.text_input("Nombre de la tarea")
            descripcion_t = st.text_area("Descripción (opcional)")
            fecha_limite_t = st.date_input("Fecha límite", value=date.today())
            submit_asg = st.form_submit_button("Asignar tarea")
            if submit_asg and sel_alumno != "---" and nombre_t:
                tareas_al = data.get("tareas", {}).get(sel_alumno, [])
                tarea = {
                    "id": len(tareas_al)+1,
                    "nombre": nombre_t,
                    "descripcion": descripcion_t,
                    "fecha_limite": str(fecha_limite_t),
                    "completada": False
                }
                tareas_al.append(tarea)
                data["tareas"][sel_alumno] = tareas_al
                guardar_datos(data)
                st.session_state.mensaje_exito = f"✅ Tarea asignada a {data['estudiantes'][sel_alumno]['nombre']}"
                st.rerun()

        st.markdown("---")
        # 3) Inscribir nuevo alumno
        st.markdown("### 👩‍🎓 Inscribir nuevo alumno")
        with st.form("inscribir_alumno"):
            nuevo_codigo = st.text_input("Código (ej UPC2025-004)")
            nuevo_nombre = st.text_input("Nombre completo")
            nuevo_activo = st.checkbox("Activo", value=True)
            permitir_crear = st.checkbox("Permitir que el alumno cree tareas", value=False)
            submit_ins = st.form_submit_button("Inscribir")
            if submit_ins:
                if not nuevo_codigo or not nuevo_nombre:
                    st.error("Completa código y nombre")
                else:
                    if nuevo_codigo in data["estudiantes"]:
                        st.error("El código ya existe")
                    else:
                        data["estudiantes"][nuevo_codigo] = {
                            "nombre": nuevo_nombre,
                            "tutor_id": st.session_state.id_tutor,
                            "activo": nuevo_activo,
                            "permitir_crear_tareas": permitir_crear
                        }
                        data["estados"][nuevo_codigo] = "inicio"
                        guardar_datos(data)
                        st.session_state.mensaje_exito = f"✅ Alumno {nuevo_nombre} inscrito correctamente"
                        st.rerun()

    # ---------------------------
    # Si rol es estudiante y visita sección tutor (mis solicitudes)
    # ---------------------------
    elif pagina == "tutor" and st.session_state.rol == "estudiante":
        st.subheader("📋 Mis solicitudes")
        mis_solicitudes = [s for s in data.get("solicitudes", []) if s["estudiante_codigo"] == st.session_state.codigo]
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
