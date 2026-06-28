# vista_trueque.py
import customtkinter as ctk
from tkinter import messagebox
from utils import cargar_imagen_ctk, formatear_reputacion, aplicar_hover_premium
class VistaTrueque(ctk.CTkFrame):
    def __init__(self, parent, sistema):
        super().__init__(parent, fg_color="transparent")
        self.sistema = sistema
        ctk.CTkLabel(
            self, text="🔄 PANEL DE TRUEQUES ACTIVOS", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#3b82f6"
        ).pack(pady=(10, 15))
        # Contenedor dividido (Izquierda: Formulario | Derecha: Slide Vertical)
        self.container_split = ctk.CTkFrame(self, fg_color="transparent")
        self.container_split.pack(fill="both", expand=True, padx=10, pady=5)
        self.container_split.grid_columnconfigure((0, 1), weight=1, uniform="column")
        self.container_split.grid_rowconfigure(0, weight=1)
        self.armar_formulario_izquierdo()
        self.armar_slide_vertical_derecho()
    def armar_formulario_izquierdo(self):
        """Formulario dinámico que lee tus pertenencias del backend."""
        self.frame_izq = ctk.CTkFrame(self.container_split, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=14)
        self.frame_izq.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        ctk.CTkLabel(self.frame_izq, text="Publicar nuevo Trueque", font=ctk.CTkFont(weight="bold", size=15), text_color="#3b82f6").pack(anchor="w", padx=20, pady=(15, 10))
        
        # --- MENÚ DESPLEGABLE DE TUS PRODUCTOS ---
        ctk.CTkLabel(self.frame_izq, text="Selecciona el producto que ofrecés:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.cb_mis_productos = ctk.CTkComboBox(self.frame_izq, values=["No tenés objetos en inventario"], border_color="#27272a", height=35)
        self.cb_mis_productos.pack(fill="x", padx=20, pady=(0, 10))
        
        # --- LO QUE BUSCÁS ---
        ctk.CTkLabel(self.frame_izq, text="¿Qué producto estás buscando a cambio?", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_busca = ctk.CTkEntry(self.frame_izq, placeholder_text="Ej: Guitarra, Reloj, Cámara...", border_color="#27272a", height=35)
        self.ent_busca.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(self.frame_izq, text="Descripción de lo que buscás:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_desc = ctk.CTkEntry(self.frame_izq, placeholder_text="Detalles del talle, marca, estado...", border_color="#27272a", height=35)
        self.ent_desc.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_publicar = ctk.CTkButton(
            self.frame_izq, text="PUBLICAR TRUEQUE", fg_color="#3b82f6", hover_color="#2563eb", 
            font=ctk.CTkFont(weight="bold", size=13), height=40, corner_radius=8, command=self.publicar_trueque
        )
        self.btn_publicar.pack(fill="x", padx=20, pady=(0, 20))
        
        self.actualizar_combo_productos()

    def actualizar_combo_productos(self):
        """Pobla y actualiza dinámicamente el dropdown de tus productos."""
        usuario = self.sistema.usuario_logueado
        if usuario:
            # Filtrar solo productos que no estén ya publicados en ventas, empeños o trueques
            lista_mis_productos = []
            for p in usuario.productos_propios:
                en_venta = any(pv.producto == p and pv.activa for pv in self.sistema.publicaciones_venta)
                en_trueque = any(pt.producto_ofrecido == p for pt in self.sistema.publicaciones_trueque)
                en_empenio = any(pe.producto == p and pe.activa for pe in self.sistema.publicaciones_empenio)
                if not (en_venta or en_trueque or en_empenio):
                    lista_mis_productos.append(p.titulo)
        else:
            lista_mis_productos = []
            
        if not lista_mis_productos:
            lista_mis_productos = ["No tenés objetos en inventario"]
            
        self.cb_mis_productos.configure(values=lista_mis_productos)
        self.cb_mis_productos.set(lista_mis_productos[0])
    def armar_slide_vertical_derecho(self):
        self.frame_der = ctk.CTkFrame(self.container_split, fg_color="transparent")
        self.frame_der.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        ctk.CTkLabel(self.frame_der, text="Chances de trueque en el mercado:", font=ctk.CTkFont(weight="bold", size=15), text_color="#cca152").pack(anchor="w", padx=5, pady=(0, 10))
        
        self.scroll_publicaciones = ctk.CTkScrollableFrame(self.frame_der, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        self.scroll_publicaciones.pack(fill="both", expand=True)
        self.actualizar_cartelera()
    def publicar_trueque(self):
        titulo_ofrecido = self.cb_mis_productos.get()
        busqueda = self.ent_busca.get()
        descripcion = self.ent_desc.get()
        
        if titulo_ofrecido == "No tenés objetos en inventario":
            messagebox.showerror("Error", "No podés hacer un trueque si no tenés objetos propios para dar.")
            return
        if not busqueda or not descripcion:
            messagebox.showwarning("Atención", "Por favor, completa los campos de lo que buscás.")
            return
        # Buscamos el objeto Producto real del usuario logueado en base al título del ComboBox
        prod_objeto = next(p for p in self.sistema.usuario_logueado.productos_propios if p.titulo == titulo_ofrecido)
        from backend import PublicacionTrueque
        # Instanciamos el objeto de trueque vinculando el producto real ofrecido
        nuevo_trueque = PublicacionTrueque(prod_objeto, busqueda, descripcion, self.sistema.usuario_logueado)
        self.sistema.publicaciones_trueque.append(nuevo_trueque)
        
        messagebox.showinfo("Éxito", f"¡Cargaste un trueque! Ofrecés tu '{titulo_ofrecido}' por '{busqueda}'.")
        
        self.ent_busca.delete(0, 'end')
        self.ent_desc.delete(0, 'end')
        self.actualizar_cartelera()
    def actualizar_cartelera(self):
        """Dibuja las cards esmeriladas leyendo el producto que dan y el que buscan."""
        for widget in self.scroll_publicaciones.winfo_children():
            widget.destroy()
            
        trueques = self.sistema.publicaciones_trueque
        query = ""
        try:
            query = self.winfo_toplevel().search_entry.get().strip().lower()
        except Exception:
            pass
        if query:
            trueques = [
                t for t in trueques
                if query in t.producto_ofrecido.titulo.lower() or query in t.producto_buscado.lower() or query in t.descripcion_busqueda.lower()
            ]
            
        if not trueques:
            ctk.CTkLabel(
                self.scroll_publicaciones, 
                text="No se encontraron trueques que coincidan." if query else "No hay trueques activos.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=40)
            return
            
        for pub in trueques:
            # CARD GLASSMORPHIC CON ACENTO AZUL NEÓN (Hover premium)
            card_glass = ctk.CTkFrame(self.scroll_publicaciones, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
            card_glass.pack(fill="x", pady=6, padx=8)
            # Usamos grid para colocar la imagen del producto ofrecido a la izquierda
            card_glass.grid_columnconfigure(0, weight=0) # Imagen del producto ofrecido
            card_glass.grid_columnconfigure(1, weight=1) # Contenido textual
            card_glass.grid_rowconfigure(0, weight=1)
            # Cargamos la imagen del producto ofrecido
            img_ctk = cargar_imagen_ctk(pub.producto_ofrecido.imagen_path, size=(75, 75))
            lbl_img = ctk.CTkLabel(card_glass, image=img_ctk, text="")
            lbl_img.grid(row=0, column=0, padx=12, pady=12, sticky="nw")
            # Contenedor para la información textual
            info_frame = ctk.CTkFrame(card_glass, fg_color="transparent")
            info_frame.grid(row=0, column=1, padx=(5, 12), pady=12, sticky="nsew")
            # Mostramos de quién es, qué da (inventario) y qué quiere cambiar
            estrellas = formatear_reputacion(pub.ofertante.reputacion)
            ctk.CTkLabel(info_frame, text=f"👤 {pub.ofertante.nombre.upper()} ({estrellas})", text_color="#cca152", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Ofrece: {pub.producto_ofrecido.titulo}", font=ctk.CTkFont(size=13, weight="normal"), text_color="#2cc985").pack(anchor="w", pady=(2, 0))
            ctk.CTkLabel(info_frame, text=f"Busca: {pub.producto_buscado}", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(info_frame, text=f"Detalle: {pub.descripcion_busqueda}", font=ctk.CTkFont(size=12), text_color="#a0a0a5", justify="left").pack(anchor="w")
            
            # Vincular click de tarjeta y hover
            aplicar_hover_premium(card_glass, "#3b82f6", original_border="#27272a")
            self.aplicar_click_tarjeta(card_glass, pub)

    def abrir_detalle(self, pub):
        from vista_detalle import VistaDetallePublicacion
        VistaDetallePublicacion(self.winfo_toplevel(), self.sistema, pub, callback_refresh=self.actualizar_cartelera)
        
    def aplicar_click_tarjeta(self, widget, pub):
        if isinstance(widget, ctk.CTkButton):
            return
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda e, p=pub: self.abrir_detalle(p))
        for child in widget.winfo_children():
            self.aplicar_click_tarjeta(child, pub)