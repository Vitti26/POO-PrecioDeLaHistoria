# vista_venta.py
import customtkinter as ctk
from tkinter import messagebox
from backend import Producto, Venta, Publicacion
from utils import cargar_imagen_ctk, notificar, formatear_reputacion, aplicar_hover_premium

class VistaVenta(ctk.CTkFrame):
    def __init__(self, parent, sistema, callback_actualizar_combos=None):
        super().__init__(parent, fg_color="transparent")
        self.sistema = sistema
        self.callback_actualizar_combos = callback_actualizar_combos
        
        # Título del panel
        ctk.CTkLabel(
            self, text="🛒 PANEL DE VENTAS Y OFERTAS", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#2cc985"
        ).pack(pady=(10, 15))
        
        # Segmented Button para pestañas
        self.tab_selector = ctk.CTkSegmentedButton(
            self, values=["Mercado de Ventas", "Mis Compras y Devoluciones"],
            selected_color="#2cc985",
            unselected_color="#18181b",
            font=ctk.CTkFont(size=13, weight="bold"), height=35,
            command=self.cambiar_pestania
        )
        self.tab_selector.pack(fill="x", padx=10, pady=(0, 15))
        
        # Contenedor para los frames dinámicos
        self.contenedor_pestania = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_pestania.pack(fill="both", expand=True)
        
        self.frames_pestanias = {}
        
        # Inicialización de las pestañas
        self.crear_tab_mercado()
        self.crear_tab_devoluciones()
        
        # Seleccionar pestaña por defecto
        self.tab_selector.set("Mercado de Ventas")
        self.cambiar_pestania("Mercado de Ventas")

    def cambiar_pestania(self, nombre):
        # Ocultar todos
        for f in self.frames_pestanias.values():
            f.pack_forget()
            
        # Mostrar el seleccionado
        frame_activo = self.frames_pestanias[nombre]
        frame_activo.pack(fill="both", expand=True)
        
        if nombre == "Mercado de Ventas":
            self.actualizar_combo_productos()
            self.actualizar_lista_mercado()
        elif nombre == "Mis Compras y Devoluciones":
            self.actualizar_compras_y_devoluciones()

    def crear_tab_mercado(self):
        f = ctk.CTkFrame(self.contenedor_pestania, fg_color="transparent")
        self.frames_pestanias["Mercado de Ventas"] = f
        
        # Layout principal dividido (Formulario + Mercado)
        self.container = ctk.CTkFrame(f, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=10, pady=5)
        self.container.grid_columnconfigure(0, weight=4) # Formulario
        self.container.grid_columnconfigure(1, weight=6) # Mercado
        self.container.grid_rowconfigure(0, weight=1)
        
        self.crear_formulario_publicacion()
        self.crear_lista_mercado()

        
    # =====================================================================
    # FORMULARIO: PUBLICAR NUEVA VENTA
    # =====================================================================
    def crear_formulario_publicacion(self):
        self.frame_izq = ctk.CTkFrame(self.container, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=14)
        self.frame_izq.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.frame_izq, text="Publicar Producto en Venta", 
            font=ctk.CTkFont(weight="bold", size=16), text_color="#2cc985"
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Selección del producto de inventario
        ctk.CTkLabel(self.frame_izq, text="Selecciona tu producto:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.cb_mis_productos = ctk.CTkComboBox(self.frame_izq, values=["Cargando..."], border_color="#27272a", height=35)
        self.cb_mis_productos.pack(fill="x", padx=20, pady=(0, 10))
        
        # Precio sugerido
        ctk.CTkLabel(self.frame_izq, text="Monto sugerido ($):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_monto = ctk.CTkEntry(self.frame_izq, placeholder_text="Ej: 45000", border_color="#27272a", height=35)
        self.ent_monto.pack(fill="x", padx=20, pady=(0, 10))
        
        # Medio de pago preferido
        ctk.CTkLabel(self.frame_izq, text="Medio de pago sugerido:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.cb_medio_pago = ctk.CTkComboBox(
            self.frame_izq, values=["Mercado Pago", "Transferencia", "Efectivo", "Tarjeta"], 
            border_color="#27272a", height=35
        )
        self.cb_medio_pago.pack(fill="x", padx=20, pady=(0, 20))
        self.cb_medio_pago.set("Mercado Pago")
        
        # Botón para publicar
        self.btn_publicar = ctk.CTkButton(
            self.frame_izq, text="PUBLICAR EN MERCADO", fg_color="#2cc985", hover_color="#22a46c", 
            text_color="#000000", font=ctk.CTkFont(weight="bold", size=13), height=40, corner_radius=8,
            command=self.publicar_venta
        )
        self.btn_publicar.pack(fill="x", padx=20, pady=(0, 20))
        
        self.actualizar_combo_productos()
        
    def actualizar_combo_productos(self):
        usuario = self.sistema.usuario_logueado
        if usuario:
            # Productos disponibles: que no estén ya publicados en ventas/trueques
            mis_productos = []
            for p in usuario.productos_propios:
                en_venta = any(pv.producto == p and pv.activa for pv in self.sistema.publicaciones_venta)
                en_trueque = any(pt.producto_ofrecido == p for pt in self.sistema.publicaciones_trueque)
                en_empenio = any(pe.producto == p and pe.activa for pe in self.sistema.publicaciones_empenio)
                if not (en_venta or en_trueque or en_empenio):
                    mis_productos.append(p.titulo)
                    
            if not mis_productos:
                mis_productos = ["No tenés objetos libres"]
                
            self.cb_mis_productos.configure(values=mis_productos)
            self.cb_mis_productos.set(mis_productos[0])
            
    def publicar_venta(self):
        titulo_prod = self.cb_mis_productos.get()
        monto_str = self.ent_monto.get().strip()
        medio = self.cb_medio_pago.get()
        
        if titulo_prod == "No tenés objetos libres":
            messagebox.showerror("Error", "No tenés ningún objeto disponible para vender en tu inventario.")
            return
            
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atención", "Por favor ingresa un monto mayor a 0.")
            return
            
        usuario = self.sistema.usuario_logueado
        prod_obj = next(p for p in usuario.productos_propios if p.titulo == titulo_prod)
        
        # Instanciar modalidad venta y publicación
        modalidad_venta = Venta(monto, medio)
        publicacion = Publicacion(prod_obj, modalidad_venta)
        
        # Guardar en sistema
        self.sistema.publicaciones_venta.append(publicacion)
        self.sistema.publicaciones_inicio.append(publicacion)
        
        # Notificaciones
        usuario.registrar_actividad(f"Ventas: Publicaste para venta el producto '{titulo_prod}' por ${monto:,.2f} con medio '{medio}'")
        notificar(usuario, f"Pusiste en venta '{titulo_prod}' por ${monto:,.2f}.", "exito")
        
        messagebox.showinfo("Venta Publicada", f"Se ha publicado con éxito '{titulo_prod}' para la venta.")
        
        self.ent_monto.delete(0, 'end')
        self.actualizar_combo_productos()
        self.actualizar_lista_mercado()
        
        if self.callback_actualizar_combos:
            self.callback_actualizar_combos()

    # =====================================================================
    # MERCADO: VENTAS ACTIVAS DE OTROS COLECCIONISTAS
    # =====================================================================
    def crear_lista_mercado(self):
        self.frame_der = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_der.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.frame_der, text="Ventas Activas en el Mercado:", 
            font=ctk.CTkFont(weight="bold", size=15), text_color="#cca152"
        ).pack(anchor="w", padx=5, pady=(0, 10))
        
        self.scroll_mercado = ctk.CTkScrollableFrame(self.frame_der, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        self.scroll_mercado.pack(fill="both", expand=True)
        self.actualizar_lista_mercado()
        
    def actualizar_lista_mercado(self):
        for widget in self.scroll_mercado.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        ventas_mercado = [p for p in self.sistema.publicaciones_venta if p.duenio != usuario and p.activa]
        
        # Filtro de búsqueda desde el navbar
        try:
            query = self.winfo_toplevel().search_entry.get().strip().lower()
            if query:
                ventas_mercado = [
                    p for p in ventas_mercado
                    if query in p.producto.titulo.lower() or query in p.producto.descripcion.lower()
                ]
        except Exception:
            pass
        if not ventas_mercado:
            ctk.CTkLabel(
                self.scroll_mercado, text="No hay productos en venta en este momento.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=40)
            return
            
        for pub in ventas_mercado:
            card = ctk.CTkFrame(self.scroll_mercado, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
            card.pack(fill="x", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=0)
            card.grid_columnconfigure(1, weight=1)
            card.grid_rowconfigure(0, weight=1)
            
            # Cargar imagen
            img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(80, 80))
            lbl_img = ctk.CTkLabel(card, image=img_ctk, text="")
            lbl_img.grid(row=0, column=0, padx=12, pady=12, sticky="nw")
            
            # Textos
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=(5, 12), pady=12, sticky="nsew")
            
            estrellas = formatear_reputacion(pub.duenio.reputacion)
            ctk.CTkLabel(info_frame, text=f"👤 Vendedor: {pub.duenio.nombre.upper()} ({estrellas})", text_color="#cca152", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=pub.producto.titulo, font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(2, 0))
            ctk.CTkLabel(info_frame, text=pub.producto.descripcion, font=ctk.CTkFont(size=11), text_color="#a0a0a5", justify="left").pack(anchor="w")
            
            ctk.CTkFrame(info_frame, height=1, fg_color="#27272a").pack(fill="x", pady=6)
            
            # Fila de Precios y Botón
            footer = ctk.CTkFrame(info_frame, fg_color="transparent")
            footer.pack(fill="x")
            
            ctk.CTkLabel(
                footer, text=f"${pub.modalidad.precio_sugerido:,.2f}\nMedio: {pub.modalidad.medio_pago_preferido}", 
                font=ctk.CTkFont(size=13, weight="bold"), text_color="#2cc985", justify="left"
            ).pack(side="left")
            
            btn_ofertar = ctk.CTkButton(
                footer, text="🤝 Ofertar / Comprar", fg_color="#2cc985", hover_color="#22a46c",
                text_color="#000000", font=ctk.CTkFont(size=11, weight="bold"), width=130, height=28,
                command=lambda p=pub: self.abrir_dialogo_oferta(p)
            )
            btn_ofertar.pack(side="right")
            
            # Vincular click de tarjeta y hover
            aplicar_hover_premium(card, "#2cc985", original_border="#27272a")
            self.aplicar_click_tarjeta(card, pub)

    def abrir_detalle(self, pub):
        from vista_detalle import VistaDetallePublicacion
        VistaDetallePublicacion(self.winfo_toplevel(), self.sistema, pub, callback_refresh=self.actualizar_lista_mercado)
        
    def aplicar_click_tarjeta(self, widget, pub):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda e, p=pub: self.abrir_detalle(p))
        for child in widget.winfo_children():
            self.aplicar_click_tarjeta(child, pub)

    # =====================================================================
    # VENTANA DIALOGO: COMPRAR O REALIZAR OFERTA
    # =====================================================================
    def abrir_dialogo_oferta(self, pub):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Realizar Oferta")
        dialog.geometry("380x260")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#09090b")
        dialog.transient(self) # Ventana sobre la principal
        dialog.grab_set()      # Bloquear clics afuera
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(
            dialog, text=f"Ofertar por:\n{pub.producto.titulo}", 
            font=ctk.CTkFont(size=15, weight="bold"), text_color="#cca152"
        ).pack(pady=(15, 10))
        
        # Campo monto
        ctk.CTkLabel(dialog, text="Tu Monto a Ofertar ($):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
        ent_monto = ctk.CTkEntry(dialog, border_color="#27272a", height=32)
        ent_monto.pack(fill="x", padx=30, pady=(2, 10))
        ent_monto.insert(0, f"{pub.modalidad.precio_sugerido:.0f}") # Autocompletar sugerido
        
        # Campo medio
        ctk.CTkLabel(dialog, text="Tu Medio de Pago:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
        cb_medio = ctk.CTkComboBox(dialog, values=["Mercado Pago", "Transferencia", "Efectivo", "Tarjeta"], border_color="#27272a", height=32)
        cb_medio.pack(fill="x", padx=30, pady=(2, 20))
        cb_medio.set(pub.modalidad.medio_pago_preferido)
        
        def enviar_oferta():
            monto_str = ent_monto.get().strip()
            medio = cb_medio.get()
            
            try:
                monto = float(monto_str)
                if monto <= 0:
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Error", "Ingresa un monto válido mayor a 0.", parent=dialog)
                return
                
            usuario_comprador = self.sistema.usuario_logueado
            
            if usuario_comprador.saldo < monto:
                messagebox.showerror("Saldo Insuficiente", f"No disponés de suficiente saldo para esta oferta. Tu saldo: ${usuario_comprador.saldo:,.2f}", parent=dialog)
                return
                
            try:
                # Registrar postulación/oferta en la publicación
                pub.postularse(usuario_comprador, monto=monto, medio_pago=medio)
                
                # Notificar a vendedor y comprador
                notificar(pub.duenio, f"{usuario_comprador.nombre} ofertó ${monto:,.2f} por tu '{pub.producto.titulo}'.", "info")
                notificar(usuario_comprador, f"Enviaste una oferta de ${monto:,.2f} por '{pub.producto.titulo}' a {pub.duenio.nombre}.", "info")
                
                messagebox.showinfo("Oferta Enviada", f"¡Enviaste tu oferta de ${monto:,.2f} correctamente! Espera la decisión de {pub.duenio.nombre}.", parent=dialog)
                dialog.destroy()
                self.actualizar_lista_mercado()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al procesar la oferta: {e}", parent=dialog)
                
        # Botones de Acción
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30)
        
        ctk.CTkButton(
            btn_frame, text="Enviar Oferta", fg_color="#2cc985", hover_color="#22a46c",
            text_color="#000000", font=ctk.CTkFont(size=12, weight="bold"), height=30, width=150,
            command=enviar_oferta
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color="#27272a", hover_color="#3f3f46",
            text_color="#ffffff", font=ctk.CTkFont(size=12), height=30, width=150,
            command=dialog.destroy
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    # =====================================================================
    # TAB: DEVOLUCIONES Y REEMBOLSOS
    # =====================================================================
    def crear_tab_devoluciones(self):
        f = ctk.CTkFrame(self.contenedor_pestania, fg_color="transparent")
        self.frames_pestanias["Mis Compras y Devoluciones"] = f
        
        self.scroll_devoluciones = ctk.CTkScrollableFrame(f, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        self.scroll_devoluciones.pack(fill="both", expand=True, padx=10, pady=10)

    def actualizar_compras_y_devoluciones(self):
        for widget in self.scroll_devoluciones.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        # --- SECCIÓN 1: MIS COMPRAS REALIZADAS ---
        ctk.CTkLabel(
            self.scroll_devoluciones, text="🛍️ Mis Compras Realizadas", 
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#cca152"
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        compras = [p for p in self.sistema.publicaciones_venta if isinstance(p.modalidad, Venta) and p.modalidad.comprador_final == usuario]
        
        if not compras:
            ctk.CTkLabel(
                self.scroll_devoluciones, text="No realizaste compras de productos todavía.", 
                font=ctk.CTkFont(size=12, slant="italic"), text_color="#71717a"
            ).pack(anchor="w", padx=25, pady=10)
        else:
            for pub in compras:
                card = ctk.CTkFrame(self.scroll_devoluciones, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
                card.pack(fill="x", padx=15, pady=6)
                
                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(fill="x", padx=15, pady=10)
                
                img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(60, 60))
                lbl_img = ctk.CTkLabel(info_frame, image=img_ctk, text="")
                lbl_img.pack(side="left", padx=(0, 15))
                
                vendedor = pub.modalidad.vendedor_final.nombre if pub.modalidad.vendedor_final else "Desconocido"
                fecha_str = pub.modalidad.fecha_compra.strftime("%d/%m/%Y %H:%M") if pub.modalidad.fecha_compra else "Desconocida"
                
                lbl_info = ctk.CTkLabel(
                    info_frame, text=f"Producto: {pub.producto.titulo}\nVendedor: {vendedor}  •  Precio pagado: ${pub.modalidad.monto_pagado:,.2f}\nFecha de Compra: {fecha_str}", 
                    justify="left", font=ctk.CTkFont(size=12)
                )
                lbl_info.pack(side="left")
                
                # Acciones de devolución
                estado = pub.modalidad.estado_devolucion
                if estado == "Disponible" or pub.modalidad.puede_solicitar_devolucion():
                    btn_devolver = ctk.CTkButton(
                        info_frame, text="Devolver Producto", fg_color="#ef4444", hover_color="#dc2626",
                        text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=120, height=28,
                        command=lambda p=pub: self.abrir_dialogo_devolucion(p)
                    )
                    btn_devolver.pack(side="right")
                elif estado == "Solicitada":
                    lbl_estado = ctk.CTkLabel(info_frame, text="⌛ Devolución Solicitada\n(Esperando respuesta)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#cca152", justify="right")
                    lbl_estado.pack(side="right")
                elif estado == "Aprobada":
                    lbl_estado = ctk.CTkLabel(info_frame, text="✅ Devolución Aprobada\n(Dinero reembolsado)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#2cc985", justify="right")
                    lbl_estado.pack(side="right")
                elif estado == "Rechazada":
                    lbl_estado = ctk.CTkLabel(info_frame, text="❌ Devolución Rechazada\n(Reclamo cerrado)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#ef4444", justify="right")
                    lbl_estado.pack(side="right")
                else:
                    # Fuera de plazo o no disponible
                    lbl_estado = ctk.CTkLabel(info_frame, text="Plazo de devolución vencido", font=ctk.CTkFont(size=11, slant="italic"), text_color="#71717a", justify="right")
                    lbl_estado.pack(side="right")
                
                # Botón de factura (siempre visible a la izquierda de la acción de devolución)
                btn_factura = ctk.CTkButton(
                    info_frame, text="📄 Factura", fg_color="#27272a", hover_color="#cca152",
                    text_color="#ffffff", font=ctk.CTkFont(size=11), width=90, height=28,
                    command=lambda p=pub: self.mostrar_factura(p)
                )
                btn_factura.pack(side="right", padx=5)
                
                # Aplicar hover premium con acento rojo para indicar posibilidad de devolución
                color_acento = "#ef4444" if estado in ["Disponible", "Solicitada"] else "#27272a"
                aplicar_hover_premium(card, color_acento, original_border="#27272a")
                    
        # --- SECCIÓN 2: SOLICITUDES DE DEVOLUCIÓN RECIBIDAS ---
        ctk.CTkLabel(
            self.scroll_devoluciones, text="📥 Solicitudes de Devolución Recibidas", 
            font=ctk.CTkFont(size=16, weight="bold"), text_color="#ef4444"
        ).pack(anchor="w", padx=15, pady=(20, 5))
        
        devoluciones_recibidas = [
            p for p in self.sistema.publicaciones_venta 
            if isinstance(p.modalidad, Venta) and p.modalidad.vendedor_final == usuario and p.modalidad.estado_devolucion == "Solicitada"
        ]
        
        if not devoluciones_recibidas:
            ctk.CTkLabel(
                self.scroll_devoluciones, text="No tenés solicitudes de devolución pendientes.", 
                font=ctk.CTkFont(size=12, slant="italic"), text_color="#71717a"
            ).pack(anchor="w", padx=25, pady=10)
        else:
            for pub in devoluciones_recibidas:
                card = ctk.CTkFrame(self.scroll_devoluciones, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
                card.pack(fill="x", padx=15, pady=6)
                
                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(fill="x", padx=15, pady=10)
                
                img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(60, 60))
                lbl_img = ctk.CTkLabel(info_frame, image=img_ctk, text="")
                lbl_img.pack(side="left", padx=(0, 15))
                
                comprador_nombre = pub.modalidad.comprador_final.nombre if pub.modalidad.comprador_final else "Desconocido"
                
                lbl_info = ctk.CTkLabel(
                    info_frame, text=f"Producto: {pub.producto.titulo}\nComprador: {comprador_nombre}  •  Precio pagado: ${pub.modalidad.monto_pagado:,.2f}\nMotivo: \"{pub.modalidad.motivo_devolucion}\"", 
                    justify="left", font=ctk.CTkFont(size=12), wraplength=400
                )
                lbl_info.pack(side="left")
                
                actions = ctk.CTkFrame(info_frame, fg_color="transparent")
                actions.pack(side="right")
                
                btn_aceptar = ctk.CTkButton(
                    actions, text="Aceptar", fg_color="#10b981", hover_color="#059669",
                    text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=80, height=24,
                    command=lambda p=pub: self.resolver_devolucion_comprador(p, aprobar=True)
                )
                btn_aceptar.pack(pady=2)
                
                btn_rechazar = ctk.CTkButton(
                    actions, text="Rechazar", fg_color="#27272a", hover_color="#ef4444",
                    text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=80, height=24,
                    command=lambda p=pub: self.resolver_devolucion_comprador(p, aprobar=False)
                )
                btn_rechazar.pack(pady=2)
                
                aplicar_hover_premium(card, "#ef4444", original_border="#27272a")

    def abrir_dialogo_devolucion(self, pub):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Solicitar Devolución")
        dialog.geometry("380x240")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#09090b")
        dialog.transient(self)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(
            dialog, text=f"Devolución de:\n{pub.producto.titulo}", 
            font=ctk.CTkFont(size=14, weight="bold"), text_color="#ef4444"
        ).pack(pady=(15, 10))
        
        ctk.CTkLabel(dialog, text="Indique el motivo de la devolución:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
        ent_motivo = ctk.CTkEntry(dialog, placeholder_text="ej: El producto tiene fallas, no funciona...", border_color="#27272a", fg_color="#18181b", height=35)
        ent_motivo.pack(fill="x", padx=30, pady=(2, 20))
        
        def enviar_solicitud():
            motivo = ent_motivo.get().strip()
            if not motivo:
                messagebox.showerror("Error", "Debe ingresar un motivo para la devolución.", parent=dialog)
                return
                
            try:
                usuario_activo = self.sistema.usuario_logueado
                pub.modalidad.solicitar_devolucion(pub, usuario_activo, motivo)
                messagebox.showinfo("Solicitud Enviada", "La solicitud de devolución fue enviada al vendedor.", parent=dialog)
                dialog.destroy()
                self.actualizar_compras_y_devoluciones()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dialog)
                
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30)
        
        ctk.CTkButton(
            btn_frame, text="Enviar Solicitud", fg_color="#ef4444", hover_color="#dc2626",
            text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=30, width=150,
            command=enviar_solicitud
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color="#27272a", hover_color="#3f3f46",
            text_color="#ffffff", font=ctk.CTkFont(size=12), height=30, width=150,
            command=dialog.destroy
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def resolver_devolucion_comprador(self, pub, aprobar: bool):
        decision = "aprobar" if aprobar else "rechazar"
        if messagebox.askyesno("Confirmar Decisión", f"¿Estás seguro de que deseas {decision} esta devolución?"):
            try:
                pub.modalidad.resolver_devolucion(pub, aprobar)
                msg_exito = "Devolución aprobada con éxito. Dinero reembolsado y producto devuelto a tu inventario." if aprobar else "Devolución rechazada con éxito."
                messagebox.showinfo("Éxito", msg_exito)
                self.actualizar_compras_y_devoluciones()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def mostrar_factura(self, pub):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Comprobante de Compra")
        dialog.geometry("450x520")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#09090b")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Invoice Header
        ctk.CTkLabel(dialog, text="EL PRECIO DE LA HISTORIA", font=ctk.CTkFont("Georgia", 20, "bold"), text_color="#cca152").pack(pady=(25, 5))
        ctk.CTkLabel(dialog, text="COMPROBANTE DE TRANSACCIÓN", font=ctk.CTkFont(size=12, weight="bold"), text_color="#a0a0a5").pack()

        # Separator line
        ctk.CTkFrame(dialog, height=1, fg_color="#27272a").pack(fill="x", padx=40, pady=15)

        # Details container
        details_frame = ctk.CTkFrame(dialog, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
        details_frame.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        # Generate a fake invoice ID based on hash of details
        factura_id = f"REF-{hash(pub.producto.titulo + str(pub.modalidad.monto_pagado)) % 10000000:08d}"
        fecha_str = pub.modalidad.fecha_compra.strftime("%d/%m/%Y %H:%M") if pub.modalidad.fecha_compra else "N/A"

        # Grid inside details
        details_frame.columnconfigure(0, weight=4)
        details_frame.columnconfigure(1, weight=6)

        rows = [
            ("Nro Factura:", factura_id),
            ("Fecha:", fecha_str),
            ("Comprador:", pub.modalidad.comprador_final.nombre if pub.modalidad.comprador_final else "N/A"),
            ("Vendedor:", pub.modalidad.vendedor_final.nombre if pub.modalidad.vendedor_final else "N/A"),
            ("Medio de Pago:", pub.modalidad.medio_pago_preferido),
            ("Estado:", pub.modalidad.estado_devolucion)
        ]

        for i, (label, val) in enumerate(rows):
            ctk.CTkLabel(details_frame, text=label, font=ctk.CTkFont(size=11, weight="bold"), text_color="#71717a", anchor="w").grid(row=i, column=0, padx=20, pady=8, sticky="w")
            ctk.CTkLabel(details_frame, text=val, font=ctk.CTkFont(size=12), text_color="#f8fafc", anchor="e").grid(row=i, column=1, padx=20, pady=8, sticky="e")

        # Line item box
        item_box = ctk.CTkFrame(details_frame, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=8)
        item_box.grid(row=len(rows), column=0, columnspan=2, padx=15, pady=15, sticky="nsew")

        ctk.CTkLabel(item_box, text=pub.producto.titulo, font=ctk.CTkFont(size=13, weight="bold"), text_color="#cca152").pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(item_box, text=pub.producto.descripcion, font=ctk.CTkFont(size=11), text_color="#a0a0a5", justify="left", wraplength=300).pack(anchor="w", padx=12, pady=(0, 8))

        # Total amount
        total_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        total_frame.pack(fill="x", padx=40, pady=(0, 20))
        ctk.CTkLabel(total_frame, text="TOTAL ABONADO:", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cca152").pack(side="left")
        ctk.CTkLabel(total_frame, text=f"${pub.modalidad.monto_pagado:,.2f}", font=ctk.CTkFont(size=18, weight="bold"), text_color="#2cc985").pack(side="right")

        # Close button
        ctk.CTkButton(
            dialog, text="Cerrar", fg_color="#27272a", hover_color="#3f3f46",
            text_color="#ffffff", font=ctk.CTkFont(size=12), height=35,
            command=dialog.destroy
        ).pack(fill="x", padx=40, pady=(0, 25))
