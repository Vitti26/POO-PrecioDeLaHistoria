# vista_empenio.py
import customtkinter as ctk
from tkinter import messagebox
from backend import Producto, Empenio, Publicacion
from utils import cargar_imagen_ctk, notificar, formatear_reputacion, aplicar_hover_premium

class VistaEmpenio(ctk.CTkFrame):
    def __init__(self, parent, sistema, callback_actualizar_combos=None):
        super().__init__(parent, fg_color="transparent")
        self.sistema = sistema
        self.callback_actualizar_combos = callback_actualizar_combos
        
        # Título del panel
        ctk.CTkLabel(
            self, text="💰 PANEL DE EMPEÑOS Y PRÉSTAMOS", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#a855f7"
        ).pack(pady=(10, 15))
        
        # Layout principal dividido
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=10, pady=5)
        self.container.grid_columnconfigure(0, weight=4) # Formulario
        self.container.grid_columnconfigure(1, weight=6) # Feed y mis prestamos
        self.container.grid_rowconfigure(0, weight=1)
        
        self.crear_formulario_publicacion()
        self.crear_panel_derecho()
        
    # =====================================================================
    # FORMULARIO: EMPEÑAR PRODUCTO PROPIO
    # =====================================================================
    def crear_formulario_publicacion(self):
        self.frame_izq = ctk.CTkFrame(self.container, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=14)
        self.frame_izq.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.frame_izq, text="Solicitar Préstamo Prendario", 
            font=ctk.CTkFont(weight="bold", size=16), text_color="#a855f7"
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Selección del producto
        ctk.CTkLabel(self.frame_izq, text="Selecciona tu producto en garantía:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.cb_mis_productos = ctk.CTkComboBox(self.frame_izq, values=["Cargando..."], border_color="#27272a", height=35)
        self.cb_mis_productos.pack(fill="x", padx=20, pady=(0, 10))
        
        # Monto solicitado
        ctk.CTkLabel(self.frame_izq, text="Monto del Préstamo ($):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_monto = ctk.CTkEntry(self.frame_izq, placeholder_text="Ej: 15000", border_color="#27272a", height=35)
        self.ent_monto.pack(fill="x", padx=20, pady=(0, 10))
        
        # Plazo solicitado
        ctk.CTkLabel(self.frame_izq, text="Plazo para pagar (días):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.cb_plazo = ctk.CTkComboBox(self.frame_izq, values=["30", "60", "90"], border_color="#27272a", height=35)
        self.cb_plazo.pack(fill="x", padx=20, pady=(0, 20))
        self.cb_plazo.set("30")
        
        # Botón para solicitar empeño
        self.btn_publicar = ctk.CTkButton(
            self.frame_izq, text="SOLICITAR FINANCIACIÓN", fg_color="#a855f7", hover_color="#9333ea", 
            text_color="#ffffff", font=ctk.CTkFont(weight="bold", size=13), height=40, corner_radius=8,
            command=self.publicar_empenio
        )
        self.btn_publicar.pack(fill="x", padx=20, pady=(0, 20))
        
        self.actualizar_combo_productos()
        
    def actualizar_combo_productos(self):
        usuario = self.sistema.usuario_logueado
        if usuario:
            # Productos disponibles: libres de cualquier publicación
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
            
    def publicar_empenio(self):
        titulo_prod = self.cb_mis_productos.get()
        monto_str = self.ent_monto.get().strip()
        plazo_str = self.cb_plazo.get()
        
        if titulo_prod == "No tenés objetos libres":
            messagebox.showerror("Error", "No tenés ningún objeto disponible para empeñar en tu inventario.")
            return
            
        try:
            monto = float(monto_str)
            if monto <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atención", "Por favor ingresa un monto de préstamo mayor a 0.")
            return
            
        try:
            plazo = int(plazo_str)
        except ValueError:
            plazo = 30
            
        usuario = self.sistema.usuario_logueado
        prod_obj = next(p for p in usuario.productos_propios if p.titulo == titulo_prod)
        
        # Instanciar empeño y publicación
        modalidad_empenio = Empenio(monto, plazo, tasa_interes=10.0) # 10% tasa fija
        publicacion = Publicacion(prod_obj, modalidad_empenio)
        
        # Registrar en el sistema
        self.sistema.publicaciones_empenio.append(publicacion)
        self.sistema.publicaciones_inicio.append(publicacion)
        
        # Actividades y notificaciones
        usuario.registrar_actividad(f"Empeños: Solicitaste un préstamo de ${monto:,.2f} a {plazo} días entregando '{titulo_prod}' en garantía.")
        notificar(usuario, f"Solicitaste empeño para '{titulo_prod}' por ${monto:,.2f}.", "exito")
        
        messagebox.showinfo("Empeño Publicado", f"Se ha publicado con éxito el empeño de '{titulo_prod}'. Espera a que un prestamista lo financie.")
        
        self.ent_monto.delete(0, 'end')
        self.actualizar_combo_productos()
        self.actualizar_feeds()
        
        if self.callback_actualizar_combos:
            self.callback_actualizar_combos()

    # =====================================================================
    # PANEL DERECHO: MERCADO DE EMPEÑOS Y MIS PRESTAMOS OTORGADOS
    # =====================================================================
    def crear_panel_derecho(self):
        self.frame_der = ctk.CTkFrame(self.container, fg_color="transparent")
        self.frame_der.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        # 1. Mercado de Empeños (Por financiar)
        ctk.CTkLabel(
            self.frame_der, text="Empeños Solicitados en el Mercado:", 
            font=ctk.CTkFont(weight="bold", size=15), text_color="#a855f7"
        ).pack(anchor="w", padx=5, pady=(0, 5))
        
        self.scroll_mercado = ctk.CTkScrollableFrame(self.frame_der, fg_color="#111116", border_width=1, border_color="#27272a", height=240, corner_radius=14)
        self.scroll_mercado.pack(fill="x", pady=(0, 15))
        
        # 2. Mis Préstamos Financiados (Dinero que presté)
        ctk.CTkLabel(
            self.frame_der, text="Mis Préstamos Otorgados (Custodias):", 
            font=ctk.CTkFont(weight="bold", size=15), text_color="#2cc985"
        ).pack(anchor="w", padx=5, pady=(0, 5))
        
        self.scroll_prestamos = ctk.CTkScrollableFrame(self.frame_der, fg_color="#111116", border_width=1, border_color="#27272a", height=200, corner_radius=14)
        self.scroll_prestamos.pack(fill="both", expand=True)
        
        self.actualizar_feeds()
        
    def actualizar_feeds(self):
        self.actualizar_mercado_empenios()
        self.actualizar_prestamos_otorgados()
        
    def actualizar_mercado_empenios(self):
        for widget in self.scroll_mercado.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        empenios_mercado = [p for p in self.sistema.publicaciones_empenio if p.duenio != usuario and p.activa and p.modalidad.estado == "Pendiente"]
        
        # Filtro de búsqueda desde el navbar
        try:
            query = self.winfo_toplevel().search_entry.get().strip().lower()
            if query:
                empenios_mercado = [
                    p for p in empenios_mercado
                    if query in p.producto.titulo.lower() or query in p.producto.descripcion.lower()
                ]
        except Exception:
            pass
        if not empenios_mercado:
            ctk.CTkLabel(
                self.scroll_mercado, text="No hay solicitudes de empeño en este momento.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=40)
            return
            
        for pub in empenios_mercado:
            card = ctk.CTkFrame(self.scroll_mercado, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
            card.pack(fill="x", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=0)
            card.grid_columnconfigure(1, weight=1)
            card.grid_rowconfigure(0, weight=1)
            
            # Imagen
            img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(65, 65))
            lbl_img = ctk.CTkLabel(card, image=img_ctk, text="")
            lbl_img.grid(row=0, column=0, padx=12, pady=10, sticky="nw")
            
            # Info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=(5, 12), pady=10, sticky="nsew")
            
            estrellas = formatear_reputacion(pub.duenio.reputacion)
            ctk.CTkLabel(info_frame, text=f"👤 Solicitante: {pub.duenio.nombre.upper()} ({estrellas})", text_color="#cca152", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Garantía: {pub.producto.titulo}", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(1, 0))
            
            # Fila de Préstamo y Botón
            footer = ctk.CTkFrame(info_frame, fg_color="transparent")
            footer.pack(fill="x", pady=(4, 0))
            
            ctk.CTkLabel(
                footer, text=f"Préstamo: ${pub.modalidad.monto_prestamo:,.2f}\nPlazo: {pub.modalidad.plazo_dias} días", 
                font=ctk.CTkFont(size=12, weight="bold"), text_color="#a855f7", justify="left"
            ).pack(side="left")
            
            btn_financiar = ctk.CTkButton(
                footer, text="🤝 Financiar (Prestar)", fg_color="#a855f7", hover_color="#9333ea",
                text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=150, height=28,
                command=lambda p=pub: self.financiar_empenio(p)
            )
            btn_financiar.pack(side="right")
            
            # Vincular click de tarjeta y hover
            aplicar_hover_premium(card, "#a855f7", original_border="#27272a")
            self.aplicar_click_tarjeta(card, pub)

    def actualizar_prestamos_otorgados(self):
        for widget in self.scroll_prestamos.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        # Préstamos otorgados por mí que sigan activos
        prestamos_otorgados = [p for p in self.sistema.publicaciones_empenio if p.modalidad.prestamista == usuario and p.modalidad.estado == "Activo"]
        if not prestamos_otorgados:
            ctk.CTkLabel(
                self.scroll_prestamos, text="No has financiado ningún empeño activo.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=30)
            return
            
        for pub in prestamos_otorgados:
            card = ctk.CTkFrame(self.scroll_prestamos, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=10)
            card.pack(fill="x", pady=4, padx=8)
            card.grid_columnconfigure(0, weight=0)
            card.grid_columnconfigure(1, weight=1)
            
            img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(55, 55))
            lbl_img = ctk.CTkLabel(card, image=img_ctk, text="")
            lbl_img.grid(row=0, column=0, padx=10, pady=8, sticky="nw")
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=(5, 10), pady=8, sticky="nsew")
            
            interes = pub.modalidad.monto_prestamo * (pub.modalidad.tasa_interes / 100.0)
            total_retorno = pub.modalidad.monto_prestamo + interes
            
            desc_text = f"Garantía en custodia: {pub.producto.titulo}\nPrestatario: {pub.duenio.nombre}  •  Capital prestado: ${pub.modalidad.monto_prestamo:,.2f}\nRetorno esperado: ${total_retorno:,.2f} (Iniciado: {pub.modalidad.fecha_inicio})"
            ctk.CTkLabel(info_frame, text=desc_text, font=ctk.CTkFont(size=11), justify="left").pack(anchor="w")
            
            # Vincular click de tarjeta y hover
            aplicar_hover_premium(card, "#2cc985", original_border="#27272a")
            self.aplicar_click_tarjeta(card, pub)

    def financiar_empenio(self, pub):
        usuario_prestamista = self.sistema.usuario_logueado
        if not usuario_prestamista:
            return
            
        monto = pub.modalidad.monto_prestamo
        if usuario_prestamista.saldo < monto:
            messagebox.showerror("Saldo Insuficiente", f"No tenés suficiente saldo para financiar este empeño de ${monto:,.2f} (Tu saldo: ${usuario_prestamista.saldo:,.2f}).")
            return
            
        pregunta = f"¿Deseas financiar el préstamo prendario para {pub.duenio.nombre}?\n\nEntregarás: ${monto:,.2f}\nRecibirás en garantía: '{pub.producto.titulo}'\nPlazo de devolución: {pub.modalidad.plazo_dias} días (+10% interés)."
        
        if messagebox.askyesno("Confirmar Financiación", pregunta):
            try:
                # Postularse como prestamista y concretar
                pub.postularse(usuario_prestamista)
                pub.seleccionar_ganador(usuario_prestamista)
                
                # Quitar publicación del feed de inicio
                if pub in self.sistema.publicaciones_inicio:
                    self.sistema.publicaciones_inicio.remove(pub)
                    
                from vista_comprobante import VistaComprobante
                VistaComprobante(self.winfo_toplevel(), pub, usuario_prestamista)
                
                # Recargar feeds
                self.actualizar_feeds()
                if self.callback_actualizar_combos:
                    self.callback_actualizar_combos()
                    
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al financiar: {e}")

    def abrir_detalle(self, pub):
        from vista_detalle import VistaDetallePublicacion
        VistaDetallePublicacion(self.winfo_toplevel(), self.sistema, pub, callback_refresh=self.actualizar_feeds)
        
    def aplicar_click_tarjeta(self, widget, pub):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda e, p=pub: self.abrir_detalle(p))
        for child in widget.winfo_children():
            self.aplicar_click_tarjeta(child, pub)
