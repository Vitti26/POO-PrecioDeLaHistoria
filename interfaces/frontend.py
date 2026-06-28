# frontend.py
import customtkinter as ctk
import tkinter as tk
from backend import SistemaPlataforma, Usuario, Producto, PublicacionTrueque, Venta, Empenio, Publicacion
from vista_trueque import VistaTrueque
from vista_cuenta import VistaCuenta
from vista_venta import VistaVenta
from vista_empenio import VistaEmpenio
from vista_faq import VistaFAQ
from utils import cargar_imagen_ctk, registrar_app_global, notificar, formatear_reputacion, aplicar_hover_premium

ctk.set_appearance_mode("dark")


class AppElPrecioDeLaHistoria(ctk.CTk):
    def __init__(self, sistema):
        super().__init__()
        self.sistema = sistema
        self.title("El Precio de la Historia")
        self.geometry("1150x720")
        self.resizable(False, False)

        # Configuración del Grid Layout principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Registrar esta app globalmente para permitir toasts desde cualquier lugar
        registrar_app_global(self)

        # Vincular el callback de notificaciones del usuario activo
        if self.sistema.usuario_logueado:
            self.sistema.usuario_logueado.app_callback = self.manejar_notificacion_entrante

        self.armar_barra_lateral()

        # Contenedor principal derecho (Navbar + Zona Contenido)
        self.right_container = ctk.CTkFrame(self, fg_color="#09090b", corner_radius=0)
        self.right_container.grid(row=0, column=1, sticky="nsew")

        self.armar_navbar()

        # Zona donde cargaremos las distintas vistas dinámicas
        self.content_area = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.content_area.pack(fill="both", expand=True)

        self.vista_actual = None
        self._vista_actual_id = "inicio"
        self.mostrar_inicio()

        # Paneles flotantes (notificaciones y chat privado), por encima de todo
        self.armar_panel_notificaciones()
        self.armar_chat_privado()
        
        # Start database polling for multi-client synchronization
        self.iniciar_monitoreo_db()

    # ==========================================
    # ARQUITECTURA GENERAL Y MENÚS DE NAVEGACIÓN
    # ==========================================
    def armar_barra_lateral(self):
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#111116", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        logo_label = ctk.CTkLabel(self.sidebar, text="EL PRECIO\nDE LA HISTORIA", font=ctk.CTkFont("Georgia", 20, "bold"), text_color="#cca152")
        logo_label.pack(pady=(30, 40))

        opciones = [
            ("🏠 Inicio", self.mostrar_inicio),
            ("🔄 Trueques", self.mostrar_trueques),
            ("💵 Ventas", self.mostrar_ventas),
            ("🔒 Empeños", self.mostrar_empenios),
            ("👤 Mi Cuenta", self.mostrar_cuenta),
            ("❓ Ayuda / FAQ", self.mostrar_faq)
        ]

        for texto, comando in opciones:
            btn = ctk.CTkButton(
                self.sidebar, text=texto, fg_color="transparent", text_color="#a0a0a5",
                font=ctk.CTkFont(size=14, weight="bold"), anchor="w", hover_color="#27272a", command=comando
            )
            btn.pack(fill="x", padx=15, pady=8)

        usuario = self.sistema.usuario_logueado
        if usuario:
            pie = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            pie.pack(side="bottom", fill="x", padx=15, pady=20)
            ctk.CTkButton(
                pie, text="🚪 Cerrar sesión", fg_color="#27272a", hover_color="#5c1d1d",
                text_color="#a0a0a5", font=ctk.CTkFont(size=12, weight="bold"), command=self.cerrar_sesion
            ).pack(fill="x")

    def cerrar_sesion(self):
        from vista_login import VistaLogin
        self.sistema.usuario_logueado.app_callback = None
        self.sistema.usuario_logueado = None
        self.destroy()
        VistaLogin(self.sistema).mainloop()

    def armar_navbar(self):
        self.navbar = ctk.CTkFrame(self.right_container, height=60, fg_color="#111116", corner_radius=0)
        self.navbar.pack(fill="x", side="top")

        # Buscador: guardado como self.search_entry para que TODAS las vistas
        # (trueque, venta, empeño e inicio) puedan filtrar en vivo contra él.
        self.search_entry = ctk.CTkEntry(self.navbar, placeholder_text="🔍 Buscar artículos...", width=300, fg_color="#27272a", border_width=0)
        self.search_entry.pack(side="left", padx=25, pady=15)
        self.search_entry.bind("<KeyRelease>", self.refrescar_busqueda)

        perfil_btn = ctk.CTkButton(self.navbar, text="👤 Perfil", width=80, fg_color="transparent", text_color="#a0a0a5", hover_color="#27272a", command=self.mostrar_cuenta)
        perfil_btn.pack(side="right", padx=15, pady=15)

        # Contenedor de notificaciones para posicionar el globo
        self.notif_container = ctk.CTkFrame(self.navbar, fg_color="transparent", width=50, height=50)
        self.notif_container.pack(side="right", padx=5, pady=5)
        self.notif_container.pack_propagate(False)

        self.notif_btn = ctk.CTkButton(
            self.notif_container, text="🔔", width=36, height=36, fg_color="transparent", text_color="#a0a0a5",
            font=ctk.CTkFont(size=18), hover_color="#27272a", command=self.toggle_notificaciones
        )
        self.notif_btn.place(relx=0.5, rely=0.5, anchor="center")

        # Globo rojo circular para las notificaciones no leídas
        self.notif_badge = ctk.CTkLabel(
            self.notif_container, text="", height=16, width=16,
            fg_color="#ef4444", text_color="#ffffff",
            font=ctk.CTkFont(size=9, weight="bold"),
            corner_radius=8
        )
        self.notif_badge.place_forget()

        # Botón de refresco manual de la app
        self.refresh_btn = ctk.CTkButton(
            self.navbar, text="🔄 Refrescar", width=90, height=32, fg_color="#27272a", hover_color="#cca152",
            text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), command=self.manual_refresh
        )
        self.refresh_btn.pack(side="right", padx=10, pady=14)

        self.actualizar_contador_notificaciones()


    def refrescar_busqueda(self, event=None):
        """Se dispara con cada tecla del buscador y refresca la vista actual."""
        if self._vista_actual_id == "inicio":
            self.mostrar_inicio()
        elif self._vista_actual_id == "trueques" and isinstance(self.vista_actual, VistaTrueque):
            self.vista_actual.actualizar_cartelera()
        elif self._vista_actual_id == "ventas" and isinstance(self.vista_actual, VistaVenta):
            self.vista_actual.actualizar_lista_mercado()
        elif self._vista_actual_id == "empenios" and isinstance(self.vista_actual, VistaEmpenio):
            self.vista_actual.actualizar_feeds()

    def manejar_notificacion_entrante(self, mensaje):
        self.actualizar_contador_notificaciones()
        if getattr(self, "panel_notif_abierto", False):
            self.poblar_panel_notificaciones()

    def actualizar_contador_notificaciones(self):
        if hasattr(self, 'notif_badge') and self.sistema.usuario_logueado:
            cant = self.sistema.usuario_logueado.cantidad_no_leidas()
            if cant > 0:
                self.notif_badge.configure(text=str(cant))
                self.notif_badge.place(relx=0.7, rely=0.25, anchor="center")
                self.notif_badge.lift()
                self.notif_btn.configure(text_color="#cca152")
            else:
                self.notif_badge.place_forget()
                self.notif_btn.configure(text_color="#a0a0a5")


    def limpiar_area_contenido(self):
        if self.vista_actual is not None:
            self.vista_actual.destroy()

    # ==========================================
    # PANEL FLOTANTE DE NOTIFICACIONES
    # ==========================================
    def armar_panel_notificaciones(self):
        self.panel_notif_abierto = False
        self.panel_notif = ctk.CTkFrame(
            self, width=360, height=450, fg_color="#18181b",
            border_width=1, border_color="#3f3f46", corner_radius=15
        )
        self.panel_notif.pack_propagate(False)



        header = ctk.CTkFrame(self.panel_notif, fg_color="#27272a", corner_radius=15)
        header.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(header, text="🔔 Notificaciones", font=ctk.CTkFont(weight="bold"), text_color="#cca152").pack(side="left", padx=15, pady=8)
        ctk.CTkButton(
            header, text="Limpiar", width=60, height=24, fg_color="transparent", hover_color="#3f3f46",
            text_color="#a0a0a5", font=ctk.CTkFont(size=10, weight="bold"), command=self.limpiar_notificaciones_panel
        ).pack(side="right", padx=5)

        self.scroll_notif_panel = ctk.CTkScrollableFrame(self.panel_notif, fg_color="#09090b", corner_radius=10)
        self.scroll_notif_panel.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def toggle_notificaciones(self):
        if self.panel_notif_abierto:
            self.panel_notif.place_forget()
            self.panel_notif_abierto = False
        else:
            # Si el chat está abierto lo cerramos para no superponerlos
            if getattr(self, "panel_chat_abierto", False):
                self.toggle_chat()
            self.panel_notif.place(relx=0.85, rely=0.13, anchor="ne")
            self.panel_notif.lift() # Asegurar que esté al frente de los contenedores
            self.panel_notif_abierto = True
            self.poblar_panel_notificaciones()
            self.sistema.usuario_logueado.marcar_notificaciones_leidas()
            self.actualizar_contador_notificaciones()

    def poblar_panel_notificaciones(self):
        for w in self.scroll_notif_panel.winfo_children():
            w.destroy()

        usuario = self.sistema.usuario_logueado
        if not usuario or not usuario.notificaciones:
            ctk.CTkLabel(self.scroll_notif_panel, text="No tenés notificaciones.", text_color="#71717a", font=ctk.CTkFont(slant="italic")).pack(pady=30)
            return

        colores = {"exito": "#2cc985", "error": "#ef4444", "info": "#3b82f6"}
        for notif in reversed(usuario.notificaciones):
            color = colores.get(notif["tipo"], "#3b82f6")
            card = ctk.CTkFrame(self.scroll_notif_panel, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=8)
            card.pack(fill="x", pady=4, padx=4)
            ctk.CTkLabel(card, text=f"⏱ {notif['hora']}", font=ctk.CTkFont(size=9), text_color=color).pack(anchor="w", padx=10, pady=(6, 0))
            
            # Usar tk.Label para evitar el truncamiento/cortado de palabras en CustomTkinter
            lbl_msg = tk.Label(
                card, text=notif["mensaje"], fg="#f1f5f9", bg="#18181b",
                font=("Segoe UI", 10), justify="left", wraplength=290
            )
            lbl_msg.pack(anchor="w", padx=10, pady=(2, 8))


    def limpiar_notificaciones_panel(self):
        if self.sistema.usuario_logueado:
            self.sistema.usuario_logueado.limpiar_notificaciones()
            self.poblar_panel_notificaciones()
            self.actualizar_contador_notificaciones()

    # ==========================================
    # CHAT PRIVADO USUARIO A USUARIO
    # ==========================================
    def armar_chat_privado(self):
        self.panel_chat_abierto = False
        self.contacto_chat_actual = None

        self.btn_chat_flotante = ctk.CTkButton(
            self, text="💬 Mensajes", width=130, height=45, corner_radius=25,
            fg_color="#3b82f6", hover_color="#2563eb", font=ctk.CTkFont(weight="bold", size=13),
            command=self.toggle_chat
        )
        self.btn_chat_flotante.place(relx=0.97, rely=0.96, anchor="se")

        self.panel_chat = ctk.CTkFrame(
            self, width=350, height=470, fg_color="#18181b",
            border_width=1, border_color="#3f3f46", corner_radius=15
        )
        self.panel_chat.pack_propagate(False)

        header_chat = ctk.CTkFrame(self.panel_chat, fg_color="#27272a", corner_radius=15)
        header_chat.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(header_chat, text="💬 Mensajes Privados", font=ctk.CTkFont(weight="bold"), text_color="#cca152").pack(side="left", padx=15, pady=8)
        ctk.CTkButton(
            header_chat, text="▼", width=30, height=30, fg_color="transparent",
            hover_color="#ef4444", text_color="white", command=self.toggle_chat
        ).pack(side="right", padx=5)

        # Selector de contacto
        selector_frame = ctk.CTkFrame(self.panel_chat, fg_color="transparent")
        selector_frame.pack(fill="x", padx=8, pady=(5, 0))
        ctk.CTkLabel(selector_frame, text="Conversar con:", font=ctk.CTkFont(size=11), text_color="#a0a0a5").pack(anchor="w")
        self.cb_contacto_chat = ctk.CTkComboBox(
            selector_frame, values=["Sin contactos"], height=32, border_color="#27272a",
            command=self.cambiar_contacto_chat
        )
        self.cb_contacto_chat.pack(fill="x", pady=(2, 8))

        # Zona scrolleable de mensajes
        self.scroll_mensajes = ctk.CTkScrollableFrame(self.panel_chat, fg_color="#09090b", corner_radius=10)
        self.scroll_mensajes.pack(fill="both", expand=True, padx=8, pady=5)

        # Entrada de texto inferior
        input_frame = ctk.CTkFrame(self.panel_chat, fg_color="transparent")
        input_frame.pack(fill="x", padx=8, pady=8)

        self.entry_chat = ctk.CTkEntry(input_frame, placeholder_text="Escribí acá...", height=35)
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_chat.bind("<Return>", lambda e: self.enviar_mensaje_chat())

        ctk.CTkButton(
            input_frame, text="➤", width=40, height=35, fg_color="#3b82f6",
            hover_color="#2563eb", command=self.enviar_mensaje_chat
        ).pack(side="right")

        self.actualizar_contactos_chat()
        self.actualizar_contador_mensajes()


    def toggle_chat(self):
        if self.panel_chat_abierto:
            self.panel_chat.place_forget()
            self.panel_chat_abierto = False
        else:
            if getattr(self, "panel_notif_abierto", False):
                self.toggle_notificaciones()
            self.actualizar_contactos_chat()
            self.panel_chat.place(relx=0.97, rely=0.88, anchor="se")
            self.panel_chat.lift() # Asegurar que esté al frente de los contenedores
            self.panel_chat_abierto = True

    def actualizar_contactos_chat(self):
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
        contactos = self.sistema.obtener_contactos(usuario)
        nombres = []
        for c in contactos:
            no_leidos = sum(1 for msg in self.sistema.mensajes_chat 
                            if msg.emisor.nombre == c.nombre and msg.receptor.nombre == usuario.nombre and not getattr(msg, "leido", False))
            if no_leidos > 0:
                nombres.append(f"{c.nombre} ({no_leidos})")
            else:
                nombres.append(c.nombre)
        
        nombres = nombres or ["Sin contactos"]
        self.cb_contacto_chat.configure(values=nombres)

        contacto_nombre_con_contador = f"{self.contacto_chat_actual.nombre} (" if self.contacto_chat_actual else ""
        match_nombre = None
        if self.contacto_chat_actual:
            for n in nombres:
                if n == self.contacto_chat_actual.nombre or n.startswith(contacto_nombre_con_contador):
                    match_nombre = n
                    break
        
        if match_nombre:
            self.cb_contacto_chat.set(match_nombre)
        else:
            self.cb_contacto_chat.set(nombres[0])
            primer_nombre = nombres[0].split(" (")[0]
            self.contacto_chat_actual = next((c for c in contactos if c.nombre == primer_nombre), None)

        self.dibujar_conversacion_actual()


    def cambiar_contacto_chat(self, nombre_elegido):
        usuario = self.sistema.usuario_logueado
        nombre_base = nombre_elegido.split(" (")[0]
        self.contacto_chat_actual = next((u for u in self.sistema.obtener_contactos(usuario) if u.nombre == nombre_base), None)
        self.dibujar_conversacion_actual()


    def dibujar_conversacion_actual(self):
        for w in self.scroll_mensajes.winfo_children():
            w.destroy()

        usuario = self.sistema.usuario_logueado
        if not usuario or not self.contacto_chat_actual:
            ctk.CTkLabel(self.scroll_mensajes, text="No hay otros usuarios registrados todavía.", text_color="#71717a", font=ctk.CTkFont(slant="italic"), wraplength=270).pack(pady=30)
            return

        self.sistema.marcar_mensajes_leidos(usuario, self.contacto_chat_actual)
        self.actualizar_contador_mensajes()

        mensajes = self.sistema.obtener_conversacion(usuario, self.contacto_chat_actual)

        if not mensajes:
            ctk.CTkLabel(self.scroll_mensajes, text=f"Todavía no chatearon con {self.contacto_chat_actual.nombre}. ¡Saludalo!", text_color="#71717a", font=ctk.CTkFont(slant="italic"), wraplength=270).pack(pady=30)
            return

        for msg in mensajes:
            es_propio = msg.emisor == usuario
            if es_propio:
                burbuja = tk.Frame(self.scroll_mensajes, bg="#3a2f1d")
                burbuja.pack(padx=(60, 10), pady=4, anchor="e")
                # Usamos tk.Label estándar para evitar truncamiento por wrapping de CustomTkinter
                lbl = tk.Label(
                    burbuja, text=msg.texto, fg="white", bg="#3a2f1d",
                    font=("Segoe UI", 11), justify="left", wraplength=200
                )
                lbl.pack(padx=10, pady=8)
            else:
                burbuja = tk.Frame(self.scroll_mensajes, bg="#27272a")
                burbuja.pack(padx=(10, 60), pady=4, anchor="w")
                # Usamos tk.Label estándar para evitar truncamiento por wrapping de CustomTkinter
                lbl_sender = tk.Label(
                    burbuja, text=f"{msg.emisor.nombre} • {msg.hora}", fg="#cca152", bg="#27272a",
                    font=("Segoe UI", 9, "bold"), justify="left"
                )
                lbl_sender.pack(anchor="w", padx=10, pady=(5, 2))
                lbl = tk.Label(
                    burbuja, text=msg.texto, fg="#a0a0a5", bg="#27272a",
                    font=("Segoe UI", 11), justify="left", wraplength=200
                )
                lbl.pack(padx=10, pady=(0, 8), anchor="w")

    def enviar_mensaje_chat(self):
        texto = self.entry_chat.get().strip()
        usuario = self.sistema.usuario_logueado
        if not texto or not usuario or not self.contacto_chat_actual:
            return

        try:
            self.sistema.enviar_mensaje(usuario, self.contacto_chat_actual, texto)
        except ValueError as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))
            return

        self.entry_chat.delete(0, "end")
        self.dibujar_conversacion_actual()

    # ==========================================
    # PANTALLA DE INICIO (CARDS MODERNAS)
    # ==========================================
    def mostrar_inicio(self):
        self._vista_actual_id = "inicio"
        self.limpiar_area_contenido()
        self.vista_actual = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.vista_actual.pack(fill="both", expand=True, padx=20, pady=20)

        saldo = self.sistema.usuario_logueado.saldo if self.sistema.usuario_logueado else 0.0

        header_frame = ctk.CTkFrame(self.vista_actual, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header_frame, text="DESCUBRÍ EL MERCADO", font=ctk.CTkFont(size=28, weight="bold"), text_color="#ffffff").pack(side="left")
        saldo_pill = ctk.CTkFrame(header_frame, fg_color="#0f2e22", corner_radius=20)
        saldo_pill.pack(side="right")
        ctk.CTkLabel(saldo_pill, text=f"💰 ${saldo:,.2f}", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2cc985").pack(padx=18, pady=8)

        scroll_mercado = ctk.CTkScrollableFrame(self.vista_actual, fg_color="transparent")
        scroll_mercado.pack(fill="both", expand=True)
        # Configurar columnas para mosaico (3 columnas de ancho proporcional)
        scroll_mercado.grid_columnconfigure(0, weight=1, minsize=280)
        scroll_mercado.grid_columnconfigure(1, weight=1, minsize=280)
        scroll_mercado.grid_columnconfigure(2, weight=1, minsize=280)

        publicaciones = [p for p in self.sistema.publicaciones_inicio if p.activa]

        query = self.search_entry.get().strip().lower() if hasattr(self, "search_entry") else ""
        if query:
            filtradas = []
            for pub in publicaciones:
                es_trueque = isinstance(pub, PublicacionTrueque)
                titulo = pub.producto.titulo.lower()
                desc = pub.producto.descripcion.lower()
                extra = pub.producto_buscado.lower() if es_trueque else ""
                if query in titulo or query in desc or query in extra:
                    filtradas.append(pub)
            publicaciones = filtradas

        if not publicaciones:
            texto_vacio = "No se encontraron publicaciones que coincidan con tu búsqueda." if query else "El mercado está tranquilo hoy. ¡Sé el primero en publicar!"
            lbl_vacio = ctk.CTkLabel(scroll_mercado, text=texto_vacio, text_color="#a0a0a5")
            lbl_vacio.grid(row=0, column=0, columnspan=3, pady=50, sticky="center")
            return

        colores_tipo = {"Venta": "#2cc985", "Empeño": "#a855f7", "Trueque": "#3b82f6"}

        for index, pub in enumerate(publicaciones):
            es_trueque = isinstance(pub, PublicacionTrueque)
            color_acento = colores_tipo.get(pub.tipo, "#cca152")

            # --- Card en mosaico vertical ---
            card = ctk.CTkFrame(scroll_mercado, fg_color="#15151a", border_width=1, border_color="#27272a", corner_radius=16, width=270, height=330)
            r = index // 3
            c = index % 3
            card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
            card.grid_propagate(False)

            # 1. Imagen del objeto centrada arriba
            img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(110, 110))
            img_frame = ctk.CTkFrame(card, fg_color="#1f1f26", corner_radius=12, width=120, height=120)
            img_frame.pack(pady=(15, 8))
            img_frame.pack_propagate(False)
            ctk.CTkLabel(img_frame, image=img_ctk, text="").place(relx=0.5, rely=0.5, anchor="center")

            # 2. Badge de tipo de publicación
            badge = ctk.CTkFrame(card, fg_color=color_acento, corner_radius=10)
            badge.pack(anchor="center", pady=(0, 6))
            tipo_txt = "🔄 TRUEQUE" if es_trueque else (f"🛒 {pub.tipo.upper()}" if pub.tipo == "Venta" else f"🔒 {pub.tipo.upper()}")
            ctk.CTkLabel(badge, text=tipo_txt, font=ctk.CTkFont(size=9, weight="bold"), text_color="#000000").pack(padx=8, pady=2)

            # 3. Título del producto
            ctk.CTkLabel(card, text=pub.producto.titulo, font=ctk.CTkFont(size=14, weight="bold"), text_color="white", wraplength=230, height=20).pack(anchor="center", padx=10)

            # 4. Dueño y Reputación
            estrellas = formatear_reputacion(pub.duenio.reputacion)
            ctk.CTkLabel(card, text=f"👤 {pub.duenio.nombre} · {estrellas}", font=ctk.CTkFont(size=10), text_color="#71717a").pack(anchor="center", pady=(1, 4))

            # 5. Valor o lo que busca
            if es_trueque:
                detalle_txt = f"Busca: {pub.producto_buscado}"
            else:
                detalle_txt = f"{pub.costo_o_plazo}"
            
            if len(detalle_txt) > 30:
                detalle_txt = detalle_txt[:27] + "..."
            ctk.CTkLabel(card, text=detalle_txt, font=ctk.CTkFont(size=12, weight="bold"), text_color=color_acento, wraplength=230).pack(anchor="center", pady=(0, 8))

            # 6. Botón de detalle
            btn_detalle = ctk.CTkButton(
                card, text="Ver Detalle →", width=160, height=30, corner_radius=8,
                fg_color="#27272a", hover_color=color_acento, text_color="#ffffff",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p=pub: self.abrir_detalle_inicio(p)
            )
            btn_detalle.pack(side="bottom", pady=(0, 15))

            aplicar_hover_premium(card, color_acento, original_border="#27272a")
            self._aplicar_click_card(card, pub)

    def _aplicar_click_card(self, widget, pub):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda e, p=pub: self.abrir_detalle_inicio(p))
        for child in widget.winfo_children():
            self._aplicar_click_card(child, pub)

    def abrir_detalle_inicio(self, pub):
        from vista_detalle import VistaDetallePublicacion
        VistaDetallePublicacion(self, self.sistema, pub, callback_refresh=self.mostrar_inicio)

    # ==========================================
    # NAVEGACIÓN ENTRE VISTAS
    # ==========================================
    def mostrar_trueques(self):
        self._vista_actual_id = "trueques"
        self.limpiar_area_contenido()
        self.vista_actual = VistaTrueque(self.content_area, self.sistema)
        self.vista_actual.pack(fill="both", expand=True)

    def mostrar_ventas(self):
        self._vista_actual_id = "ventas"
        self.limpiar_area_contenido()
        self.vista_actual = VistaVenta(self.content_area, self.sistema, callback_actualizar_combos=self.mostrar_ventas)
        self.vista_actual.pack(fill="both", expand=True)

    def mostrar_empenios(self):
        self._vista_actual_id = "empenios"
        self.limpiar_area_contenido()
        self.vista_actual = VistaEmpenio(self.content_area, self.sistema, callback_actualizar_combos=self.mostrar_empenios)
        self.vista_actual.pack(fill="both", expand=True)

    def mostrar_cuenta(self):
        self._vista_actual_id = "cuenta"
        self.limpiar_area_contenido()
        self.vista_actual = VistaCuenta(self.content_area, self.sistema)
        self.vista_actual.pack(fill="both", expand=True)

    def mostrar_faq(self):
        self._vista_actual_id = "faq"
        self.limpiar_area_contenido()
        self.vista_actual = VistaFAQ(self.content_area)
        self.vista_actual.pack(fill="both", expand=True)

    def iniciar_monitoreo_db(self):
        try:
            token_antes = self.sistema.last_update_token
            self.sistema.cargar_db()
            token_despues = self.sistema.last_update_token
            
            # If database changed, refresh the whole UI
            if token_antes != token_despues:

                # Re-bind active user reference
                if self.sistema.usuario_logueado:
                    logged_in_name = self.sistema.usuario_logueado.nombre
                    new_logged_in = self.sistema.usuarios.get(logged_in_name)
                    if new_logged_in:
                        new_logged_in.app_callback = self.manejar_notificacion_entrante
                        self.sistema.usuario_logueado = new_logged_in
                
                # Refresh notifications
                self.actualizar_contador_notificaciones()
                if getattr(self, "panel_notif_abierto", False):
                    self.poblar_panel_notificaciones()
                
                # Refresh chat
                self.actualizar_contador_mensajes()
                if getattr(self, "panel_chat_abierto", False):
                    self.actualizar_contactos_chat()
                else:
                    self.actualizar_contactos_chat()
                
                # Refresh current active view
                self.refrescar_vista_actual()

        except Exception as e:
            print(f"Error en monitoreo de base de datos: {e}")
            
        self.after(1500, self.iniciar_monitoreo_db)

    def refrescar_vista_actual(self):
        if self._vista_actual_id == "inicio":
            self.mostrar_inicio()
        elif self._vista_actual_id == "trueques" and hasattr(self.vista_actual, "actualizar_cartelera"):
            self.vista_actual.actualizar_cartelera()
        elif self._vista_actual_id == "ventas" and hasattr(self.vista_actual, "actualizar_lista_mercado"):
            self.vista_actual.actualizar_lista_mercado()
        elif self._vista_actual_id == "empenios" and hasattr(self.vista_actual, "actualizar_feeds"):
            self.vista_actual.actualizar_feeds()
        elif self._vista_actual_id == "cuenta" and hasattr(self.vista_actual, "cambiar_pestania"):
            current_tab = self.vista_actual.tab_selector.get()
            self.vista_actual.cambiar_pestania(current_tab)

    def manual_refresh(self):
        try:
            self.sistema.last_mtime = 0.0
            self.sistema.cargar_db()
            
            if self.sistema.usuario_logueado:
                logged_in_name = self.sistema.usuario_logueado.nombre
                new_logged_in = self.sistema.usuarios.get(logged_in_name)
                if new_logged_in:
                    new_logged_in.app_callback = self.manejar_notificacion_entrante
                    self.sistema.usuario_logueado = new_logged_in
            
            self.actualizar_contador_notificaciones()
            if getattr(self, "panel_notif_abierto", False):
                self.poblar_panel_notificaciones()
                
            self.actualizar_contador_mensajes()
            self.actualizar_contactos_chat()
            self.refrescar_vista_actual()
            notificar(self.sistema.usuario_logueado, "Sincronización de datos completada", "exito")
        except Exception as e:
            print(f"Error en refresco manual: {e}")

    def actualizar_contador_mensajes(self):
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
        cant = self.sistema.cantidad_mensajes_no_leidos(usuario)
        if cant > 0:
            self.btn_chat_flotante.configure(
                text=f"💬 Mensajes ({cant})",
                fg_color="#ef4444",
                hover_color="#dc2626"
            )
        else:
            self.btn_chat_flotante.configure(
                text="💬 Mensajes",
                fg_color="#3b82f6",
                hover_color="#2563eb"
            )