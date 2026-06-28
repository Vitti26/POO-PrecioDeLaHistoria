# vista_detalle.py
import customtkinter as ctk
from tkinter import messagebox
from backend import Producto, Venta, Empenio, Publicacion, PublicacionTrueque
from utils import cargar_imagen_ctk, notificar, formatear_reputacion

class VistaDetallePublicacion(ctk.CTkToplevel):
    def __init__(self, parent, sistema, publicacion, callback_refresh=None):
        super().__init__(parent)
        self.sistema = sistema
        self.publicacion = publicacion
        self.callback_refresh = callback_refresh
        
        self.title("Detalles de la Publicación")
        self.geometry("620x580")
        self.resizable(False, False)
        self.configure(fg_color="#09090b")
        
        self.transient(parent) # Ventana flotante vinculada
        self.grab_set()      # Bloquear clics fuera
        
        # Resolver datos según tipo de publicación (Trueque vs Venta/Empeño)
        self.es_trueque = hasattr(publicacion, 'producto_ofrecido')
        
        if self.es_trueque:
            self.producto = publicacion.producto_ofrecido
            self.duenio = publicacion.ofertante
            self.tipo_str = "Trueque"
        else:
            self.producto = publicacion.producto
            self.duenio = publicacion.duenio
            self.tipo_str = publicacion.tipo
            
        # Centrar ventana
        self.update_idletasks()
        x = parent.winfo_toplevel().winfo_x() + (parent.winfo_toplevel().winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_toplevel().winfo_y() + (parent.winfo_toplevel().winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self.armar_layout()
        
    def armar_layout(self):
        # Grid layout de 2 columnas principales
        self.grid_columnconfigure(0, weight=4) # Imagen
        self.grid_columnconfigure(1, weight=6) # Textos y Acciones
        self.grid_rowconfigure(0, weight=1)
        
        # --- COLUMNA IZQUIERDA (Imagen) ---
        izq = ctk.CTkFrame(self, fg_color="transparent")
        izq.grid(row=0, column=0, padx=20, pady=25, sticky="nsew")
        
        # Imagen principal ampliada
        img_ctk = cargar_imagen_ctk(self.producto.imagen_path, size=(200, 200))
        lbl_img = ctk.CTkLabel(izq, image=img_ctk, text="")
        lbl_img.pack(pady=20, anchor="center")
        
        # Estado/Modalidad Badge
        if self.tipo_str == "Venta":
            color_badge = "#2cc985"
            texto_badge = "🛒 EN VENTA"
        elif self.tipo_str == "Trueque":
            color_badge = "#3b82f6"
            texto_badge = "🔄 TRUEQUE"
        else:
            color_badge = "#a855f7"
            texto_badge = "💰 EMPEÑO"
            
        badge_frame = ctk.CTkFrame(izq, fg_color=color_badge, corner_radius=6, height=30)
        badge_frame.pack_propagate(False)
        badge_frame.pack(fill="x", padx=15)
        ctk.CTkLabel(badge_frame, text=texto_badge, font=ctk.CTkFont(size=12, weight="bold"), text_color="#000000").pack(expand=True)
        
        # --- COLUMNA DERECHA (Detalles y Acciones) ---
        der = ctk.CTkFrame(self, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        der.grid(row=0, column=1, padx=20, pady=25, sticky="nsew")
        
        # Título
        ctk.CTkLabel(der, text=self.producto.titulo, font=ctk.CTkFont(size=18, weight="bold"), text_color="#ffffff", wraplength=320, justify="left").pack(anchor="w", padx=20, pady=(20, 5))
        
        # Descripción
        ctk.CTkLabel(der, text=self.producto.descripcion, font=ctk.CTkFont(size=12), text_color="#a0a0a5", wraplength=320, justify="left").pack(anchor="w", padx=20, pady=(0, 10))
        
        ctk.CTkFrame(der, height=1, fg_color="#27272a").pack(fill="x", padx=20, pady=5)
        
        # Datos del Propietario y su Reputación
        ctk.CTkLabel(der, text="👤 Propietario:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#71717a").pack(anchor="w", padx=20, pady=(5, 0))
        
        lbl_duenio_nombre = ctk.CTkLabel(der, text=f"{self.duenio.nombre} (Coleccionista)", font=ctk.CTkFont(size=13, weight="bold"), text_color="#cca152")
        lbl_duenio_nombre.pack(anchor="w", padx=20)
        
        # Mostrar estrellas de reputación
        estrellas_str = formatear_reputacion(self.duenio.reputacion)
        lbl_reputacion = ctk.CTkLabel(
            der, text=f"Reputación: {estrellas_str}  •  {self.duenio.transacciones_completadas} transacciones", 
            font=ctk.CTkFont(size=11), text_color="#a0a0a5"
        )
        lbl_reputacion.pack(anchor="w", padx=20, pady=(0, 10))
        
        ctk.CTkFrame(der, height=1, fg_color="#27272a").pack(fill="x", padx=20, pady=5)
        
        # Contenedor dinámico según Modalidad
        self.acciones_frame = ctk.CTkFrame(der, fg_color="transparent")
        self.acciones_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.cargar_controles_acciones()
        
    def cargar_controles_acciones(self):
        usuario_activo = self.sistema.usuario_logueado
        
        # Caso 1: Es un trueque
        if self.es_trueque:
            ctk.CTkLabel(self.acciones_frame, text=f"Lo que busca: {self.publicacion.producto_buscado}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#3b82f6").pack(anchor="w", pady=2)
            ctk.CTkLabel(self.acciones_frame, text=f"Detalles: {self.publicacion.descripcion_busqueda}", font=ctk.CTkFont(size=11), text_color="#a0a0a5", justify="left", wraplength=300).pack(anchor="w", pady=(0, 15))
            
            if self.duenio == usuario_activo:
                ctk.CTkLabel(self.acciones_frame, text="🟢 Esta es tu publicación de trueque.", font=ctk.CTkFont(size=12, slant="italic"), text_color="#3b82f6").pack(pady=10)
            else:
                ctk.CTkLabel(self.acciones_frame, text="Proponer uno de tus productos:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
                
                # Cargar productos libres del usuario logueado
                mis_productos = []
                for p in usuario_activo.productos_propios:
                    en_venta = any(pv.producto == p and pv.activa for pv in self.sistema.publicaciones_venta)
                    en_trueque = any(pt.producto_ofrecido == p for pt in self.sistema.publicaciones_trueque)
                    en_empenio = any(pe.producto == p and pe.activa for pe in self.sistema.publicaciones_empenio)
                    if not (en_venta or en_trueque or en_empenio):
                        mis_productos.append(p.titulo)
                        
                if not mis_productos:
                    ctk.CTkLabel(self.acciones_frame, text="No tenés ningún producto libre para ofrecer.", text_color="#ef4444", font=ctk.CTkFont(size=11, slant="italic")).pack(pady=5)
                else:
                    cb_mis_prods = ctk.CTkComboBox(self.acciones_frame, values=mis_productos, border_color="#27272a", height=32, width=280)
                    cb_mis_prods.pack(pady=(2, 12))
                    cb_mis_prods.set(mis_productos[0])
                    
                    def aceptar_trueque_click():
                        prod_ofrecido_nombre = cb_mis_prods.get()
                        prod_ofrecido_obj = next(p for p in usuario_activo.productos_propios if p.titulo == prod_ofrecido_nombre)
                        
                        if messagebox.askyesno("Confirmar Trueque", f"¿Deseas intercambiar tu '{prod_ofrecido_nombre}' por el/la '{self.producto.titulo}' de {self.duenio.nombre}?"):
                            # Ejecutar intercambio de trueque
                            # Quitar productos y transferir dueños
                            self.duenio.remover_producto(self.producto)
                            usuario_activo.remover_producto(prod_ofrecido_obj)
                            
                            self.duenio.agregar_producto(prod_ofrecido_obj)
                            usuario_activo.agregar_producto(self.producto)
                            
                            # Incrementar transacciones
                            self.duenio.transacciones_completadas += 1
                            usuario_activo.transacciones_completadas += 1
                            
                            # Eliminar publicacion de trueque
                            if self.publicacion in self.sistema.publicaciones_trueque:
                                self.sistema.publicaciones_trueque.remove(self.publicacion)
                            if self.publicacion in self.sistema.publicaciones_inicio:
                                self.sistema.publicaciones_inicio.remove(self.publicacion)
                                
                            # Historial e informes
                            self.duenio.registrar_actividad(f"Trueque: Cambiaste tu {self.producto.titulo} por {prod_ofrecido_nombre} de {usuario_activo.nombre}")
                            usuario_activo.registrar_actividad(f"Trueque: Cambiaste tu {prod_ofrecido_nombre} por {self.producto.titulo} de {self.duenio.nombre}")
                            
                            notificar(self.duenio, f"¡Trueque concretado! {usuario_activo.nombre} aceptó cambiar '{self.producto.titulo}' por '{prod_ofrecido_nombre}'.", "exito")
                            notificar(usuario_activo, f"¡Trueque concretado! Cambiaste '{prod_ofrecido_nombre}' por '{self.producto.titulo}'.", "exito")
                            
                            messagebox.showinfo("Éxito", "¡Intercambio realizado con éxito!")
                            self.destroy()
                            if self.callback_refresh:
                                self.callback_refresh()
                                
                    ctk.CTkButton(
                        self.acciones_frame, text="🤝 Proponer Intercambio", fg_color="#3b82f6", hover_color="#2563eb",
                        text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=35,
                        command=aceptar_trueque_click
                    ).pack(fill="x", pady=2)
                    
        # Caso 2: Es una Venta
        elif self.tipo_str == "Venta":
            ctk.CTkLabel(self.acciones_frame, text=f"Precio sugerido: ${self.publicacion.modalidad.precio_sugerido:,.2f}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#2cc985").pack(anchor="w", pady=1)
            ctk.CTkLabel(self.acciones_frame, text=f"Medio de pago sugerido: {self.publicacion.modalidad.medio_pago_preferido}", font=ctk.CTkFont(size=11), text_color="#a0a0a5").pack(anchor="w", pady=(0, 15))
            
            if self.duenio == usuario_activo:
                ctk.CTkLabel(self.acciones_frame, text="🟢 Esta es tu publicación de venta.", font=ctk.CTkFont(size=12, slant="italic"), text_color="#2cc985").pack(pady=5)
                
                # Breve listado de ofertas en el modal
                ofertas = self.publicacion.modalidad.ofertas_list
                if ofertas:
                    ctk.CTkLabel(self.acciones_frame, text="Ofertas recibidas:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", pady=(5, 2))
                    for ofr in ofertas:
                        if ofr.estado == "Pendiente":
                            ofr_fr = ctk.CTkFrame(self.acciones_frame, fg_color="#1c1c24", border_width=1, border_color="#27272a")
                            ofr_fr.pack(fill="x", pady=2)
                            ctk.CTkLabel(ofr_fr, text=f"{ofr.comprador.nombre}: ${ofr.monto:,.0f} ({ofr.medio_pago})", font=ctk.CTkFont(size=11)).pack(side="left", padx=8, pady=4)
                            
                            def aceptar_ofr_click(u=ofr.comprador):
                                try:
                                    self.publicacion.seleccionar_ganador(u)
                                    if self.publicacion in self.sistema.publicaciones_inicio:
                                        self.sistema.publicaciones_inicio.remove(self.publicacion)
                                    notificar(u, f"¡Tu oferta por '{self.producto.titulo}' fue aceptada!", "exito")
                                    
                                    from vista_comprobante import VistaComprobante
                                    VistaComprobante(self.master, self.publicacion, u)
                                    
                                    self.destroy()
                                    if self.callback_refresh:
                                        self.callback_refresh()
                                except Exception as err:
                                    messagebox.showerror("Error", str(err))
                                    
                            ctk.CTkButton(
                                ofr_fr, text="Aceptar", fg_color="#10b981", hover_color="#059669",
                                width=60, height=22, font=ctk.CTkFont(size=10, weight="bold"),
                                command=aceptar_ofr_click
                            ).pack(side="right", padx=5)
            else:
                # Formulario para ofertar
                ctk.CTkLabel(self.acciones_frame, text="Tu oferta ($):", font=ctk.CTkFont(size=11)).pack(anchor="w")
                ent_ofr = ctk.CTkEntry(self.acciones_frame, border_color="#27272a", height=30)
                ent_ofr.pack(fill="x", pady=(2, 8))
                ent_ofr.insert(0, f"{self.publicacion.modalidad.precio_sugerido:.0f}")
                
                cb_medio = ctk.CTkComboBox(self.acciones_frame, values=["Mercado Pago", "Transferencia", "Efectivo", "Tarjeta"], border_color="#27272a", height=30)
                cb_medio.pack(fill="x", pady=(0, 15))
                cb_medio.set(self.publicacion.modalidad.medio_pago_preferido)
                
                def enviar_oferta_click():
                    monto_str = ent_ofr.get().strip()
                    medio = cb_medio.get()
                    try:
                        monto = float(monto_str)
                        if monto <= 0: raise ValueError()
                    except ValueError:
                        messagebox.showerror("Error", "Ingresa un monto válido mayor a 0.")
                        return
                        
                    if usuario_activo.saldo < monto:
                        messagebox.showerror("Saldo Insuficiente", f"No tenés suficiente saldo. Saldo actual: ${usuario_activo.saldo:,.2f}")
                        return
                        
                    try:
                        self.publicacion.postularse(usuario_activo, monto=monto, medio_pago=medio)
                        notificar(self.duenio, f"{usuario_activo.nombre} ofertó ${monto:,.2f} por tu '{self.producto.titulo}'.", "info")
                        notificar(usuario_activo, f"Enviaste una oferta de ${monto:,.2f} por '{self.producto.titulo}' a {self.duenio.nombre}.", "info")
                        messagebox.showinfo("Éxito", f"¡Oferta de ${monto:,.2f} enviada con éxito!")
                        self.destroy()
                        if self.callback_refresh:
                            self.callback_refresh()
                    except Exception as err:
                        messagebox.showerror("Error", str(err))
                        
                ctk.CTkButton(
                    self.acciones_frame, text="🤝 Enviar Oferta", fg_color="#2cc985", hover_color="#22a46c",
                    text_color="#000000", font=ctk.CTkFont(size=12, weight="bold"), height=35,
                    command=enviar_oferta_click
                ).pack(fill="x")
                
        # Caso 3: Es un Empeño
        elif self.tipo_str == "Empeño":
            ctk.CTkLabel(self.acciones_frame, text=f"Préstamo solicitado: ${self.publicacion.modalidad.monto_prestamo:,.2f}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#a855f7").pack(anchor="w", pady=1)
            ctk.CTkLabel(self.acciones_frame, text=f"Plazo solicitado: {self.publicacion.modalidad.plazo_dias} días  •  Interés: {self.publicacion.modalidad.tasa_interes}%", font=ctk.CTkFont(size=11), text_color="#a0a0a5").pack(anchor="w", pady=(0, 20))
            
            if self.duenio == usuario_activo:
                ctk.CTkLabel(self.acciones_frame, text="🟢 Esta es tu solicitud de empeño.", font=ctk.CTkFont(size=12, slant="italic"), text_color="#a855f7").pack(pady=10)
            else:
                def financiar_empenio_click():
                    monto = self.publicacion.modalidad.monto_prestamo
                    if usuario_activo.saldo < monto:
                        messagebox.showerror("Saldo Insuficiente", f"No tenés suficiente saldo para financiar este empeño. Saldo actual: ${usuario_activo.saldo:,.2f}")
                        return
                        
                    msg = f"¿Deseas financiar el préstamo prendario de {self.duenio.nombre}?\n\nEntregarás: ${monto:,.2f}\nRecibirás en garantía: '{self.producto.titulo}'\nPlazo de devolución: {self.publicacion.modalidad.plazo_dias} días (+{self.publicacion.modalidad.tasa_interes}% de interés)."
                    if messagebox.askyesno("Confirmar Financiación", msg):
                        try:
                            self.publicacion.postularse(usuario_activo)
                            self.publicacion.seleccionar_ganador(usuario_activo)
                            
                            if self.publicacion in self.sistema.publicaciones_inicio:
                                self.sistema.publicaciones_inicio.remove(self.publicacion)
                                
                            from vista_comprobante import VistaComprobante
                            VistaComprobante(self.master, self.publicacion, usuario_activo)
                            
                            self.destroy()
                            if self.callback_refresh:
                                self.callback_refresh()
                        except Exception as err:
                            messagebox.showerror("Error", str(err))
                            
                ctk.CTkButton(
                    self.acciones_frame, text="🤝 Financiar Empeño (Prestar)", fg_color="#a855f7", hover_color="#9333ea",
                    text_color="#ffffff", font=ctk.CTkFont(size=12, weight="bold"), height=35,
                    command=financiar_empenio_click
                ).pack(fill="x")

        # Botón para abrir chat privado con el dueño de la publicación
        if self.duenio != usuario_activo:
            def abrir_chat():
                app = self.master.winfo_toplevel()
                app.contacto_chat_actual = self.duenio
                app.actualizar_contactos_chat()
                if not app.panel_chat_abierto:
                    app.toggle_chat()
                app.cb_contacto_chat.set(self.duenio.nombre)
                app.cambiar_contacto_chat(self.duenio.nombre)

            ctk.CTkButton(
                self.acciones_frame,
                text="💬 Enviar mensaje",
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                text_color="white",
                font=ctk.CTkFont(size=12, weight="bold"),
                height=35,
                command=abrir_chat
            ).pack(fill="x", pady=(10, 0))

