import streamlit as st
from datetime import datetime

# === INICIALIZACIÓN GLOBAL (una sola vez) ===
if "inicializado" not in st.session_state:
    # Lista de tutores disponibles
    st.session_state.tutores_disponibles = [
        {"id": "tutor_juan", "nombre": "Juan Pérez"},
        {"id": "tutor_ana", "nombre": "Ana López"},
        {"id": "tutor_carlos", "nombre": "Carlos Méndez"}
    ]
    
    # Solicitudes globales (persisten entre sesiones del navegador)
    st.session_state.solicitudes_asesoria = []
    
    # Mensajes del sistema
    st.session_state.mensajes_sistema = ["¡Bienvenido/a al sistema de apoyo anti-procrastinación!"]
    
    st.session_state.inicializado = True

# === Estado del usuario (se reinicia al cerrar sesión) ===
if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False
    st.session_state.rol = None
    st.session_state.nombre = ""
    st.session_state.curso = ""
    st.session_state.id_tutor = None
    st.session_state.pagina_actual = "inicio"

# === Perfiles de acceso ===
PERFILES = {
    "ESTUDIANTE-01": {
        "rol": "estudiante",
        "nombre": "María García",
        "curso": "Maestría en Innovación Educativa"
    },
    "TUTOR-JUAN": {
        "rol": "tutor",
        "nombre": "Juan Pérez",
        "curso": "Maestría en Innovación Educativa",
        "id_tutor": "tutor_juan"
    },
    "TUTOR-ANA": {
        "rol": "tutor",
        "nombre": "Ana López",
        "curso": "Maestría en Innovación Educativa",
        "id_tutor": "tutor_ana"
    }
}

# === PANTALLA DE ACCESO ===
if not st.session_state.usuario_autenticado:
    st.set_page_config(page_title="Apoyo Anti-Procrastinación", layout="centered")
    st.title("🎓 Apoyo Anti-Procrastinación")
    st.markdown("Este recurso está disponible solo para estudiantes y tutores referidos.")
    codigo = st.text_input("Ingresa tu código de acceso", placeholder="Ej: ESTUDIANTE-01")
    
    if st.button("Ingresar"):
        if codigo in PERFILES:
            perfil = PERFILES[codigo]
            st.session_state.usuario_autenticado = True
            st.session_state.rol = perfil["rol"]
            st.session_state.nombre = perfil["nombre"]
            st.session_state.curso = perfil["curso"]
            if perfil["rol"] == "tutor":
                st.session_state.id_tutor = perfil["id_tutor"]
            st.rerun()
        else:
            st.error("Código inválido. Contacta a tu coordinador.")
    
    st.info("Códigos de prueba:\n- Estudiante: `ESTUDIANTE-01`\n- Tutor Juan: `TUTOR-JUAN`\n- Tutor Ana: `TUTOR-ANA`")

# === APP PRINCIPAL ===
else:
    st.set_page_config(page_title=f"{st.session_state.nombre} - Apoyo", layout="centered")
    
    # Barra superior con cierre de sesión
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.title(f"👋 {st.session_state.nombre}")
        st.caption(f"{st.session_state.curso}")
    with col_logout:
        if st.button("🚪 Cerrar sesión"):
            st.session_state.usuario_autenticado = False
            st.session_state.rol = None
            st.session_state.nombre = ""
            st.session_state.curso = ""
            st.session_state.id_tutor = None
            st.rerun()

    # Navegación
    st.markdown("---")
    col_nav = st.columns(4)
    with col_nav[0]:
        if st.button("🏠 Inicio"):
            st.session_state.pagina_actual = "inicio"
    with col_nav[1]:
        if st.button("✅ Tareas"):
            st.session_state.pagina_actual = "tareas"
    with col_nav[2]:
        if st.button("🆘 Asesoría"):
            st.session_state.pagina_actual = "asesoria"
    with col_nav[3]:
        if st.button("👨‍🏫 Tutor" if st.session_state.rol == "estudiante" else "📊 Mis solicitudes"):
            st.session_state.pagina_actual = "tutor"

    # === PÁGINA: Inicio ===
    if st.session_state.pagina_actual == "inicio":
        st.subheader("Selecciona una opción")
        st.info(st.session_state.mensajes_sistema[-1])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Mis tareas", use_container_width=True):
                st.session_state.pagina_actual = "tareas"
                st.rerun()
        with col2:
            if st.button("🆘 Solicitar asesoría", use_container_width=True):
                st.session_state.pagina_actual = "asesoria"
                st.rerun()

    # === PÁGINA: Tareas ===
    elif st.session_state.pagina_actual == "tareas":
        st.subheader("📌 Mis tareas")
        if "tareas_usuario" not in st.session_state:
            st.session_state.tareas_usuario = []
        
        nueva_tarea = st.text_input("Nombre de la tarea")
        fecha_limite = st.date_input("Fecha límite")
        if st.button("➕ Añadir tarea"):
            if nueva_tarea.strip():
                st.session_state.tareas_usuario.append({
                    "id": len(st.session_state.tareas_usuario) + 1,
                    "nombre": nueva_tarea,
                    "fecha_limite": str(fecha_limite),
                    "completada": False
                })
                st.success("✅ Tarea añadida")
                st.rerun()
        
        # Mostrar tareas
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

    # === PÁGINA: Asesoría (estudiante) ===
    elif st.session_state.pagina_actual == "asesoria" and st.session_state.rol == "estudiante":
        st.subheader("🆘 Solicitar asesoría")
        st.markdown("Selecciona un tutor y describe tu necesidad.")
        
        nombres_tutores = [t["nombre"] for t in st.session_state.tutores_disponibles]
        tutor_seleccionado_nombre = st.selectbox("Tutor asignado", nombres_tutores)
        tutor_seleccionado = next(t for t in st.session_state.tutores_disponibles if t["nombre"] == tutor_seleccionado_nombre)
        
        mensaje = st.text_area("Describe tu necesidad (máx. 200 caracteres)", max_chars=200)
        if st.button("📤 Enviar solicitud"):
            if mensaje.strip():
                nueva_solicitud = {
                    "id": len(st.session_state.solicitudes_asesoria) + 1,
                    "estudiante": st.session_state.nombre,
                    "id_tutor": tutor_seleccionado["id"],
                    "nombre_tutor": tutor_seleccionado["nombre"],
                    "mensaje": mensaje,
                    "fecha_envio": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "fecha_aceptacion": None,
                    "estado": "pendiente"
                }
                st.session_state.solicitudes_asesoria.append(nueva_solicitud)
                st.success("✅ Solicitud enviada. Tu tutor será notificado.")

    # === PÁGINA: Tutor ===
    elif st.session_state.pagina_actual == "tutor":
        if st.session_state.rol == "tutor":
            st.subheader("📬 Solicitudes pendientes")
            mis_solicitudes = [
                s for s in st.session_state.solicitudes_asesoria 
                if s["id_tutor"] == st.session_state.id_tutor and s["estado"] == "pendiente"
            ]
            
            if mis_solicitudes:
                for s in mis_solicitudes:
                    with st.container():
                        st.markdown(f"**Estudiante:** {s['estudiante']}")
                        st.markdown(f"**Mensaje:** {s['mensaje']}")
                        st.caption(f"Enviado: {s['fecha_envio']}")
                        if st.button("✅ Aceptar solicitud", key=f"aceptar_{s['id']}"):
                            s["fecha_aceptacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            s["estado"] = "aceptada"
                            st.success("✅ Sesión de asesoría programada")
                            st.rerun()
                        st.divider()
            else:
                st.info("No tienes solicitudes pendientes.")
            
            # Historial
            st.subheader("📋 Historial de asesorías")
            historial = [s for s in st.session_state.solicitudes_asesoria if s["id_tutor"] == st.session_state.id_tutor and s["estado"] == "aceptada"]
            if historial:
                for s in historial:
                    st.markdown(f"- **{s['estudiante']}** | {s['fecha_aceptacion']}")
            else:
                st.caption("Aún no has aceptado solicitudes.")
                
        else:  # Estudiante viendo el estado de sus solicitudes
            st.subheader("📋 Mis solicitudes de asesoría")
            mis_solicitudes = [s for s in st.session_state.solicitudes_asesoria if s["estudiante"] == st.session_state.nombre]
            if mis_solicitudes:
                for s in mis_solicitudes:
                    estado = "✅ Aceptada" if s["estado"] == "aceptada" else "⏳ Pendiente"
                    st.markdown(f"**Tutor:** {s['nombre_tutor']} | **Estado:** {estado}")
                    st.caption(f"Enviado: {s['fecha_envio']}")
                    if s["fecha_aceptacion"]:
                        st.caption(f"Aceptada: {s['fecha_aceptacion']}")
                    st.divider()
            else:
                st.info("No has enviado solicitudes de asesoría.")
