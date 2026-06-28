# vista_cuenta.py
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from backend import Producto, Venta, Empenio
from utils import cargar_imagen_ctk, notificar, formatear_reputacion, aplicar_hover_premium

class VistaCuenta(ctk.CTkFrame):
    def __init__(self, parent, sistema, callback_actualizar_combos=None):
        super().__init__(parent, fg_color="transparent")
        self.sistema = sistema
        self.callback_actualizar_combos = callback_actualizar_combos
        self.ruta_imagen_seleccionada = None
        
        # Título principal
        ctk.CTkLabel(
            self, text="👤 MI CUENTA Y CONTROL DE COLECCIONISTA", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#cca152"
        ).pack(pady=(10, 15))
        
        # Botón Segmentado para pestañas
        self.tab_selector = ctk.CTkSegmentedButton(
            self, values=["Mi Perfil", "Mi Inventario", "Mis Actividades", "Historial"],
            selected_color="#cca152",
            unselected_color="#18181b",
            font=ctk.CTkFont(size=13, weight="bold"), height=35,
            command=self.cambiar_pestania
        )
        self.tab_selector.pack(fill="x", padx=10, pady=(0, 15))
        
        # Contenedor para los frames dinámicos
        self.contenedor_pestania = ctk.CTkFrame(self, fg_color="transparent")
        self.contenedor_pestania.pack(fill="both", expand=True)
        
        # Inicialización de los frames de pestañas
        self.frames_pestanias = {}
        self.crear_tab_perfil()
        self.crear_tab_inventario()
        self.crear_tab_actividades()
        self.crear_tab_historial()
        
        # Seleccionar pestaña por defecto
        self.tab_selector.set("Mi Perfil")
        self.cambiar_pestania("Mi Perfil")
        
    def cambiar_pestania(self, nombre):
        # Ocultar todos
        for f in self.frames_pestanias.values():
            f.pack_forget()
            
        # Mostrar el seleccionado
        frame_activo = self.frames_pestanias[nombre]
        frame_activo.pack(fill="both", expand=True)
        
        # Actualizar contenido específico
        if nombre == "Mi Perfil":
            self.actualizar_perfil_campos()
            self.actualizar_notificaciones()
        elif nombre == "Mi Inventario":
            self.actualizar_lista_productos()
        elif nombre == "Mis Actividades":
            self.actualizar_actividades()
        elif nombre == "Historial":
            self.actualizar_historial()
            
    # =====================================================================
    # 1. PESTAÑA: MI PERFIL Y VINCULACIÓN BANCARIA
    # =====================================================================
    def crear_tab_perfil(self):
        f = ctk.CTkFrame(self.contenedor_pestania, fg_color="transparent")
        self.frames_pestanias["Mi Perfil"] = f
        
        f.grid_columnconfigure(0, weight=5) # Formulario
        f.grid_columnconfigure(1, weight=5) # Notificaciones
        f.grid_rowconfigure(0, weight=1)
        
        # --- Formulario de Edición (Izquierda) ---
        izq = ctk.CTkFrame(f, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=14)
        izq.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        
        self.scroll_perfil = ctk.CTkScrollableFrame(izq, fg_color="transparent")
        self.scroll_perfil.pack(fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(
            self.scroll_perfil, text="Mi Perfil de Coleccionista", 
            font=ctk.CTkFont(weight="bold", size=16), text_color="#cca152"
        ).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Foto de Perfil / Avatar
        self.avatar_frame = ctk.CTkFrame(self.scroll_perfil, fg_color="transparent")
        self.avatar_frame.pack(fill="x", padx=15, pady=5)
        
        self.lbl_avatar = ctk.CTkLabel(self.avatar_frame, text="")
        self.lbl_avatar.pack(side="left", padx=(0, 15))
        
        avatar_controls = ctk.CTkFrame(self.avatar_frame, fg_color="transparent")
        avatar_controls.pack(side="left", fill="both", expand=True)
        
        self.btn_cargar_avatar = ctk.CTkButton(
            avatar_controls, text="📷 Cambiar Foto", fg_color="#27272a", hover_color="#3f3f46",
            text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), height=25,
            command=self.cambiar_avatar
        )
        self.btn_cargar_avatar.pack(anchor="w", pady=2)
        
        # Nombre (Editable)
        ctk.CTkLabel(self.scroll_perfil, text="Nombre del Coleccionista:", font=ctk.CTkFont(size=11), text_color="#a0a0a5").pack(anchor="w", padx=15, pady=(8, 1))
        self.ent_nombre = ctk.CTkEntry(self.scroll_perfil, border_color="#27272a", height=35, font=ctk.CTkFont(size=13))
        self.ent_nombre.pack(fill="x", padx=15, pady=(0, 10))
        
        # Info Reputación (Lectura)
        self.reputacion_frame = ctk.CTkFrame(self.scroll_perfil, fg_color="transparent")
        self.reputacion_frame.pack(fill="x", padx=15, pady=5)
        
        self.lbl_reputacion_perfil = ctk.CTkLabel(self.reputacion_frame, text="Reputación: ", justify="left", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_reputacion_perfil.pack(anchor="w")
        
        self.btn_guardar_perfil = ctk.CTkButton(
            self.scroll_perfil, text="GUARDAR CAMBIOS", fg_color="#cca152", hover_color="#b58c42",
            text_color="#000000", font=ctk.CTkFont(weight="bold", size=12), height=35, corner_radius=8,
            command=self.guardar_perfil
        )
        self.btn_guardar_perfil.pack(fill="x", padx=15, pady=(10, 10))
        
        ctk.CTkFrame(self.scroll_perfil, height=1, fg_color="#27272a").pack(fill="x", padx=15, pady=10)
        
        # Sección Banco
        ctk.CTkLabel(
            self.scroll_perfil, text="🏦 Cuenta Bancaria y Tarjetas", 
            font=ctk.CTkFont(weight="bold", size=14), text_color="#cca152"
        ).pack(anchor="w", padx=15, pady=(5, 5))
        
        self.bank_info_frame = ctk.CTkFrame(self.scroll_perfil, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=10)
        self.bank_info_frame.pack(fill="x", padx=15, pady=5)
        
        self.lbl_banco_detalles = ctk.CTkLabel(self.bank_info_frame, text="Cargando...", justify="left", font=ctk.CTkFont(size=12))
        self.lbl_banco_detalles.pack(anchor="w", padx=15, pady=12)
        
        self.btn_banco_accion = ctk.CTkButton(
            self.scroll_perfil, text="VINCULAR BANCO", fg_color="#cca152", hover_color="#b58c42",
            text_color="#000000", font=ctk.CTkFont(weight="bold", size=12), height=38, corner_radius=8,
            command=self.gestionar_banco
        )
        self.btn_banco_accion.pack(fill="x", padx=15, pady=(5, 20))
        
        # --- Centro de Notificaciones (Derecha) ---
        der = ctk.CTkFrame(f, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        der.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        header_notif = ctk.CTkFrame(der, fg_color="transparent")
        header_notif.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            header_notif, text="🔔 Notificaciones", 
            font=ctk.CTkFont(weight="bold", size=16), text_color="#cca152"
        ).pack(side="left")
        
        self.btn_limpiar_notif = ctk.CTkButton(
            header_notif, text="Limpiar", fg_color="#27272a", hover_color="#3f3f46",
            text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=60, height=25,
            command=self.limpiar_notificaciones
        )
        self.btn_limpiar_notif.pack(side="right")
        
        self.scroll_notificaciones = ctk.CTkScrollableFrame(der, fg_color="transparent")
        self.scroll_notificaciones.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
    def cambiar_avatar(self):
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
        tipos_archivos = [("Imágenes", "*.png *.jpg *.jpeg *.webp")]
        ruta = filedialog.askopenfilename(title="Seleccionar foto de perfil", filetypes=tipos_archivos)
        if ruta:
            usuario.avatar_path = ruta
            usuario.registrar_actividad("Perfil: Modificaste tu foto de perfil")
            notificar(usuario, "Foto de perfil actualizada.", "exito")
            self.actualizar_perfil_campos()
            if self.callback_actualizar_combos:
                self.callback_actualizar_combos()
                
    def actualizar_perfil_campos(self):
        usuario = self.sistema.usuario_logueado
        if usuario:
            self.ent_nombre.delete(0, 'end')
            self.ent_nombre.insert(0, usuario.nombre)
            
            # Cargar imagen avatar
            img_ctk = cargar_imagen_ctk(usuario.avatar_path, size=(60, 60))
            self.lbl_avatar.configure(image=img_ctk)
            
            # Reputación estrellas y saldo
            estrellas = formatear_reputacion(usuario.reputacion)
            self.lbl_reputacion_perfil.configure(
                text=f"Valoración: {estrellas}\nIntercambios concretados: {usuario.transacciones_completadas}\nSaldo en Cartera: ${usuario.saldo:,.2f}"
            )
            
            # Banco vinculación
            if usuario.banco_vinculado:
                tarjeta_oculta = f"**** **** **** {usuario.tarjeta_nro[-4:]}" if len(usuario.tarjeta_nro) >= 4 else "****"
                detalles = f"🏦 Entidad: {usuario.banco_nombre}\nAlias / CBU: '{usuario.cbu_alias}'\nTarjeta vinculada: {tarjeta_oculta}"
                self.lbl_banco_detalles.configure(text=detalles, text_color="#2cc985")
                self.btn_banco_accion.configure(text="💵 DEPOSITAR / CARGAR SALDO", fg_color="#2cc985", hover_color="#22a46c")
            else:
                self.lbl_banco_detalles.configure(text="No tenés ninguna cuenta bancaria vinculada.\nDebes vincular una cuenta para poder cargar saldo.", text_color="#71717a")
                self.btn_banco_accion.configure(text="🏦 VINCULAR BANCO Y TARJETA", fg_color="#cca152", hover_color="#b58c42")
                
    def gestionar_banco(self):
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        if not usuario.banco_vinculado:
            # Modal para vincular banco
            dialog = ctk.CTkToplevel(self)
            dialog.title("Vincular Cuenta Bancaria / Tarjeta")
            dialog.geometry("380x440")
            dialog.resizable(False, False)
            dialog.configure(fg_color="#09090b")
            dialog.transient(self)
            dialog.grab_set()
            
            # Centrar
            dialog.update_idletasks()
            x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            ctk.CTkLabel(dialog, text="🏦 Vincular Cuenta Bancaria", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cca152").pack(pady=15)
            
            ctk.CTkLabel(dialog, text="Selecciona tu Banco:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
            cb_banco = ctk.CTkComboBox(dialog, values=["Banco Galicia", "Santander Río", "BBVA", "Mercado Pago", "Banco Nación"], border_color="#27272a", height=30)
            cb_banco.pack(fill="x", padx=30, pady=(2, 8))
            cb_banco.set("Banco Galicia")
            
            ctk.CTkLabel(dialog, text="CBU o Alias de Cuenta:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
            ent_alias = ctk.CTkEntry(dialog, placeholder_text="ej: alias.banco.trueque", border_color="#27272a", height=30)
            ent_alias.pack(fill="x", padx=30, pady=(2, 8))
            
            ctk.CTkLabel(dialog, text="Últimos 4 dígitos de Tarjeta:", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
            ent_tarjeta = ctk.CTkEntry(dialog, placeholder_text="ej: 4321", border_color="#27272a", height=30)
            ent_tarjeta.pack(fill="x", padx=30, pady=(2, 8))
            
            ctk.CTkLabel(dialog, text="Saldo Inicial a depositar ($):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=30)
            ent_saldo_ini = ctk.CTkEntry(dialog, placeholder_text="ej: 50000", border_color="#27272a", height=30)
            ent_saldo_ini.pack(fill="x", padx=30, pady=(2, 15))
            ent_saldo_ini.insert(0, "50000")
            
            def confirmar_vinculo():
                banco = cb_banco.get()
                alias = ent_alias.get().strip()
                tarjeta = ent_tarjeta.get().strip()
                saldo_ini_str = ent_saldo_ini.get().strip()
                
                if not alias or not tarjeta:
                    messagebox.showerror("Error", "Por favor completa el Alias y la Tarjeta.", parent=dialog)
                    return
                try:
                    saldo_ini = float(saldo_ini_str)
                    if saldo_ini < 0: raise ValueError()
                except ValueError:
                    messagebox.showerror("Error", "Ingresa un saldo inicial válido.", parent=dialog)
                    return
                    
                usuario.vincular_banco(banco, alias, tarjeta, saldo_ini)
                notificar(usuario, f"Cuenta vinculada con éxito. Fondos acreditados: ${saldo_ini:,.2f}", "exito")
                messagebox.showinfo("Éxito", "¡Tu cuenta bancaria ha sido vinculada!", parent=dialog)
                dialog.destroy()
                self.actualizar_perfil_campos()
                if self.callback_actualizar_combos:
                    self.callback_actualizar_combos()
                    
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(fill="x", padx=30, pady=(10, 20))
            ctk.CTkButton(btn_frame, text="Vincular", fg_color="#cca152", hover_color="#b58c42", text_color="#000000", font=ctk.CTkFont(weight="bold"), height=30, command=confirmar_vinculo).pack(side="left", expand=True, fill="x", padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#27272a", hover_color="#3f3f46", text_color="#ffffff", height=30, command=dialog.destroy).pack(side="right", expand=True, fill="x", padx=(5, 0))
            
        else:
            # Depositar fondos
            dialog = ctk.CTkToplevel(self)
            dialog.title("Depositar Fondos")
            dialog.geometry("340x260")
            dialog.resizable(False, False)
            dialog.configure(fg_color="#09090b")
            dialog.transient(self)
            dialog.grab_set()
            
            # Centrar
            dialog.update_idletasks()
            x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            ctk.CTkLabel(dialog, text="💵 Depositar Fondos", font=ctk.CTkFont(size=14, weight="bold"), text_color="#2cc985").pack(pady=15)
            
            ctk.CTkLabel(dialog, text=f"Desde: {usuario.banco_nombre} (Alias '{usuario.cbu_alias}')", font=ctk.CTkFont(size=11), text_color="#a0a0a5").pack()
            
            ctk.CTkLabel(dialog, text="Monto a Transferir ($):", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=40, pady=(10, 2))
            ent_deposito = ctk.CTkEntry(dialog, placeholder_text="ej: 10000", border_color="#27272a", height=32)
            ent_deposito.pack(fill="x", padx=40, pady=(0, 15))
            ent_deposito.insert(0, "10000")
            
            def confirmar_deposito():
                monto_str = ent_deposito.get().strip()
                try:
                    monto = float(monto_str)
                    if monto <= 0: raise ValueError()
                except ValueError:
                    messagebox.showerror("Error", "Ingresa un monto válido mayor a 0.", parent=dialog)
                    return
                    
                try:
                    usuario.depositar_fondos(monto)
                    notificar(usuario, f"Depósito completado. Acreditaste ${monto:,.2f}.", "exito")
                    messagebox.showinfo("Éxito", f"¡Se acreditaron ${monto:,.2f} con éxito!", parent=dialog)
                    dialog.destroy()
                    self.actualizar_perfil_campos()
                    if self.callback_actualizar_combos:
                        self.callback_actualizar_combos()
                except Exception as err:
                    messagebox.showerror("Error", str(err), parent=dialog)
                    
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(fill="x", padx=40, pady=(10, 20))
            ctk.CTkButton(btn_frame, text="Acreditar", fg_color="#2cc985", hover_color="#22a46c", text_color="#000000", font=ctk.CTkFont(weight="bold"), height=30, command=confirmar_deposito).pack(side="left", expand=True, fill="x", padx=(0, 5))
            ctk.CTkButton(btn_frame, text="Cancelar", fg_color="#27272a", hover_color="#3f3f46", text_color="#ffffff", height=30, command=dialog.destroy).pack(side="right", expand=True, fill="x", padx=(5, 0))

    def guardar_perfil(self):
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
        
        nuevo_nombre = self.ent_nombre.get().strip()
        
        if not nuevo_nombre:
            messagebox.showwarning("Error", "El nombre no puede estar vacío.")
            return
            
        viejo_nombre = usuario.nombre
        usuario.nombre = nuevo_nombre
        
        # Registrar en actividades y notificar
        usuario.registrar_actividad(f"Perfil: Cambiaste tu nombre de '{viejo_nombre}' a '{nuevo_nombre}'")
        notificar(usuario, "Nombre de perfil actualizado correctamente.", "exito")
        
        messagebox.showinfo("Éxito", "Perfil guardado correctamente.")
        
        if self.callback_actualizar_combos:
            self.callback_actualizar_combos()
            
    def actualizar_notificaciones(self):
        for widget in self.scroll_notificaciones.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario or not usuario.notificaciones:
            ctk.CTkLabel(
                self.scroll_notificaciones, text="No tenés notificaciones nuevas.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=40)
            return
            
        # Mostrar de la más nueva a la más vieja
        for notif in reversed(usuario.notificaciones):
            color_tipo = "#2cc985" if notif["tipo"] == "exito" else ("#ef4444" if notif["tipo"] == "error" else "#3b82f6")
            
            card = ctk.CTkFrame(self.scroll_notificaciones, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=10)
            card.pack(fill="x", pady=4, padx=5)
            
            # Encabezado (Hora y punto indicador de estado)
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=(8, 2))
            
            ctk.CTkLabel(header, text=f"⏱ {notif['hora']}", font=ctk.CTkFont(size=10), text_color="#71717a").pack(side="left")
            
            # Mensaje
            ctk.CTkLabel(
                card, text=notif["mensaje"], font=ctk.CTkFont(size=12), 
                text_color="#f8fafc", justify="left", wraplength=250
            ).pack(anchor="w", padx=10, pady=(2, 8))
            
            # Acotado indicador visual lateral
            marcador = ctk.CTkFrame(card, width=4, height=30, fg_color=color_tipo)
            marcador.pack_propagate(False)
            marcador.place(relx=0, rely=0.2, anchor="w")
            
            notif["leida"] = True # Marcamos como leída una vez visualizada
            
    def limpiar_notificaciones(self):
        usuario = self.sistema.usuario_logueado
        if usuario:
            usuario.limpiar_notificaciones()
            self.actualizar_notificaciones()

    # =====================================================================
    # 2. PESTAÑA: MI INVENTARIO (REGISTRO Y LISTADO)
    # =====================================================================
    def crear_tab_inventario(self):
        f = ctk.CTkFrame(self.contenedor_pestania, fg_color="transparent")
        self.frames_pestanias["Mi Inventario"] = f
        
        f.grid_columnconfigure(0, weight=4) # Formulario
        f.grid_columnconfigure(1, weight=6) # Lista
        f.grid_rowconfigure(0, weight=1)
        
        # --- Formulario Izquierdo ---
        self.frame_izq_inv = ctk.CTkFrame(f, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=14)
        self.frame_izq_inv.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.frame_izq_inv, text="Registrar Nuevo Objeto", 
            font=ctk.CTkFont(weight="bold", size=16), text_color="#cca152"
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(self.frame_izq_inv, text="Nombre / Título del Objeto:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_titulo = ctk.CTkEntry(self.frame_izq_inv, placeholder_text="Ej: Moneda Romana, PlayStation 1...", border_color="#27272a", height=35)
        self.ent_titulo.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(self.frame_izq_inv, text="Descripción y estado:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.ent_descripcion = ctk.CTkEntry(self.frame_izq_inv, placeholder_text="Detalla el estado físico, antigüedad...", border_color="#27272a", height=35)
        self.ent_descripcion.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(self.frame_izq_inv, text="Foto del Objeto:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=20, pady=(5, 2))
        self.image_select_frame = ctk.CTkFrame(self.frame_izq_inv, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=10)
        self.image_select_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.preview_image = cargar_imagen_ctk(None, size=(100, 100))
        self.lbl_preview = ctk.CTkLabel(self.image_select_frame, image=self.preview_image, text="")
        self.lbl_preview.pack(pady=10)
        
        self.btn_seleccionar_foto = ctk.CTkButton(
            self.image_select_frame, text="📁 Seleccionar Foto", fg_color="#27272a", hover_color="#3f3f46", 
            text_color="#ffffff", font=ctk.CTkFont(weight="bold", size=12), height=30, command=self.seleccionar_foto
        )
        self.btn_seleccionar_foto.pack(pady=(0, 10))
        
        self.btn_registrar = ctk.CTkButton(
            self.frame_izq_inv, text="AÑADIR AL INVENTARIO", fg_color="#cca152", hover_color="#b58c42", 
            text_color="#000000", font=ctk.CTkFont(weight="bold", size=13), height=40, corner_radius=8,
            command=self.registrar_producto
        )
        self.btn_registrar.pack(fill="x", padx=20, pady=(5, 20))
        
        # --- Lista Derecha ---
        self.frame_der_inv = ctk.CTkFrame(f, fg_color="transparent")
        self.frame_der_inv.grid(row=0, column=1, padx=15, pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.frame_der_inv, text="Mis Objetos Registrados:", 
            font=ctk.CTkFont(weight="bold", size=15), text_color="#cca152"
        ).pack(anchor="w", padx=5, pady=(0, 10))
        
        self.scroll_productos = ctk.CTkScrollableFrame(self.frame_der_inv, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        self.scroll_productos.pack(fill="both", expand=True)
        
    def seleccionar_foto(self):
        tipos_archivos = [("Imágenes", "*.png *.jpg *.jpeg *.webp")]
        ruta = filedialog.askopenfilename(title="Seleccionar foto del objeto", filetypes=tipos_archivos)
        if ruta:
            self.ruta_imagen_seleccionada = ruta
            self.preview_image = cargar_imagen_ctk(ruta, size=(100, 100))
            self.lbl_preview.configure(image=self.preview_image)
            
    def registrar_producto(self):
        titulo = self.ent_titulo.get().strip()
        descripcion = self.ent_descripcion.get().strip()
        if not titulo or not descripcion:
            messagebox.showwarning("Campos incompletos", "Por favor, completa el título y la descripción del objeto.")
            return
            
        usuario_activo = self.sistema.usuario_logueado
        nuevo_prod = Producto(titulo, descripcion, usuario_activo)
        
        if self.ruta_imagen_seleccionada:
            nuevo_prod.definir_imagen(self.ruta_imagen_seleccionada)
            
        usuario_activo.registrar_actividad(f"Inventario: Añadiste '{titulo}' a tu inventario")
        notificar(usuario_activo, f"Registraste '{titulo}' en tu inventario.", "exito")
        
        # Limpiar
        self.ent_titulo.delete(0, 'end')
        self.ent_descripcion.delete(0, 'end')
        self.ruta_imagen_seleccionada = None
        self.preview_image = cargar_imagen_ctk(None, size=(100, 100))
        self.lbl_preview.configure(image=self.preview_image)
        
        # Recargar
        self.actualizar_lista_productos()
        if self.callback_actualizar_combos:
            self.callback_actualizar_combos()
            
    def actualizar_lista_productos(self):
        for widget in self.scroll_productos.winfo_children():
            widget.destroy()
            
        usuario_activo = self.sistema.usuario_logueado
        if not usuario_activo or not usuario_activo.productos_propios:
            ctk.CTkLabel(
                self.scroll_productos, text="No tenés ningún objeto registrado en tu inventario.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=40)
            return
            
        for prod in usuario_activo.productos_propios:
            card = ctk.CTkFrame(self.scroll_productos, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=12)
            card.pack(fill="x", pady=6, padx=8)
            card.grid_columnconfigure(0, weight=0)
            card.grid_columnconfigure(1, weight=1)
            card.grid_rowconfigure(0, weight=1)
            
            img_ctk = cargar_imagen_ctk(prod.imagen_path, size=(80, 80))
            lbl_img = ctk.CTkLabel(card, image=img_ctk, text="")
            lbl_img.grid(row=0, column=0, padx=12, pady=12, sticky="w")
            
            text_frame = ctk.CTkFrame(card, fg_color="transparent")
            text_frame.grid(row=0, column=1, padx=(5, 12), pady=12, sticky="nsew")
            
            ctk.CTkLabel(text_frame, text=prod.titulo, font=ctk.CTkFont(size=14, weight="bold"), text_color="#cca152").pack(anchor="w")
            ctk.CTkLabel(text_frame, text=prod.descripcion, font=ctk.CTkFont(size=12), text_color="#a0a0a5", justify="left").pack(anchor="w", pady=(2, 0))
            
            # Ver si el producto está en una publicación activa en este momento
            en_venta = any(p.producto == prod and p.activa for p in self.sistema.publicaciones_venta)
            en_trueque = any(p.producto_ofrecido == prod for p in self.sistema.publicaciones_trueque)
            en_empenio = any(p.producto == prod and p.activa for p in self.sistema.publicaciones_empenio)
            
            if en_venta:
                estado_text = "🟠 PUBLICADO EN VENTA"
                estado_color = "#2cc985"
            elif en_trueque:
                estado_text = "🔵 PUBLICADO EN TRUEQUE"
                estado_color = "#3b82f6"
            elif en_empenio:
                estado_text = "🟣 EMPEÑADO EN CUSTODIA"
                estado_color = "#a855f7"
            else:
                estado_text = "🟢 DISPONIBLE EN INVENTARIO"
                estado_color = "#cca152"
                
            ctk.CTkLabel(text_frame, text=estado_text, font=ctk.CTkFont(size=10, weight="bold"), text_color=estado_color).pack(anchor="w", pady=(4, 0))
            
            # Aplicar hover premium con el color del estado actual
            aplicar_hover_premium(card, estado_color, original_border="#27272a")

    # =====================================================================
    # 3. PESTAÑA: MIS ACTIVIDADES ACTIVAS (SEGUIMIENTO Y GESTIÓN)
    # =====================================================================
    def crear_tab_actividades(self):
        f = ctk.CTkScrollableFrame(self.contenedor_pestania, fg_color="transparent")
        self.frames_pestanias["Mis Actividades"] = f
        
    def actualizar_actividades(self):
        f = self.frames_pestanias["Mis Actividades"]
        for widget in f.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        # --- 3.1. MIS VENTAS Y OFERTAS RECIBIDAS ---
        ctk.CTkLabel(f, text="🛒 Mis Ventas Activas y Ofertas Recibidas", font=ctk.CTkFont(size=16, weight="bold"), text_color="#2cc985").pack(anchor="w", padx=10, pady=(10, 5))
        
        mis_ventas = [p for p in self.sistema.publicaciones_venta if p.duenio == usuario and p.activa]
        if not mis_ventas:
            ctk.CTkLabel(f, text="No tenés ninguna publicación de venta activa.", font=ctk.CTkFont(size=12, slant="italic"), text_color="#71717a").pack(anchor="w", padx=25, pady=10)
        else:
            for pub in mis_ventas:
                card = ctk.CTkFrame(f, fg_color="#18181b", border_width=1, border_color="#2cc985", corner_radius=12)
                card.pack(fill="x", padx=10, pady=5)
                
                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(fill="x", padx=15, pady=10)
                
                # Imagen del producto
                img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(60, 60))
                lbl_img = ctk.CTkLabel(info_frame, image=img_ctk, text="")
                lbl_img.pack(side="left", padx=(0, 15))
                
                # Info
                lbl_info = ctk.CTkLabel(
                    info_frame, text=f"Producto: {pub.producto.titulo}\nPrecio sugerido: $ {pub.modalidad.precio_sugerido:,.2f}  •  Medio preferido: {pub.modalidad.medio_pago_preferido}", 
                    justify="left", font=ctk.CTkFont(size=13, weight="bold")
                )
                lbl_info.pack(side="left")
                
                # Botón para cancelar la venta
                btn_cancelar = ctk.CTkButton(
                    info_frame, text="Cancelar Publicación", fg_color="#5c1d1d", hover_color="#ef4444",
                    text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=120, height=28,
                    command=lambda p=pub: self.cancelar_publicacion_venta(p)
                )
                btn_cancelar.pack(side="right")
                
                # Ofertas recibidas para esta venta
                ctk.CTkLabel(card, text="   Ofertas recibidas para este producto:", font=ctk.CTkFont(size=11, weight="bold", slant="italic"), text_color="#a0a0a5").pack(anchor="w", padx=15, pady=(5, 2))
                
                ofertas = pub.modalidad.ofertas_list
                if not ofertas:
                    ctk.CTkLabel(card, text="      Aún no se han recibido ofertas.", font=ctk.CTkFont(size=11, slant="italic"), text_color="#71717a").pack(anchor="w", padx=20, pady=(2, 10))
                else:
                    for ofr in ofertas:
                        ofr_card = ctk.CTkFrame(card, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=8)
                        ofr_card.pack(fill="x", padx=20, pady=3)
                        
                        lbl_ofr = ctk.CTkLabel(
                            ofr_card, text=f"👤 {ofr.comprador.nombre} ofrece ${ofr.monto:,.2f} pagando con {ofr.medio_pago} [Estado: {ofr.estado}]",
                            font=ctk.CTkFont(size=12)
                        )
                        lbl_ofr.pack(side="left", padx=10, pady=8)
                        
                        if ofr.estado == "Pendiente":
                            # Botones Aceptar / Rechazar
                            actions = ctk.CTkFrame(ofr_card, fg_color="transparent")
                            actions.pack(side="right", padx=10)
                            
                            btn_aceptar = ctk.CTkButton(
                                actions, text="Aceptar", fg_color="#10b981", hover_color="#059669",
                                text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=70, height=24,
                                command=lambda p=pub, u=ofr.comprador: self.aceptar_oferta(p, u)
                            )
                            btn_aceptar.pack(side="left", padx=3)
                            
                            btn_rechazar = ctk.CTkButton(
                                actions, text="Rechazar", fg_color="#27272a", hover_color="#ef4444",
                                text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=70, height=24,
                                command=lambda o=ofr, c=card: self.rechazar_oferta(o)
                            )
                            btn_rechazar.pack(side="left", padx=3)
                            
        # --- 3.2. MIS TRUEQUES ACTIVOS ---
        ctk.CTkLabel(f, text="🔄 Mis Trueques Activos", font=ctk.CTkFont(size=16, weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=10, pady=(20, 5))
        
        mis_trueques = [p for p in self.sistema.publicaciones_trueque if p.ofertante == usuario]
        if not mis_trueques:
            ctk.CTkLabel(f, text="No tenés ninguna publicación de trueque activa.", font=ctk.CTkFont(size=12, slant="italic"), text_color="#71717a").pack(anchor="w", padx=25, pady=10)
        else:
            for pub in mis_trueques:
                card = ctk.CTkFrame(f, fg_color="#18181b", border_width=1, border_color="#3b82f6", corner_radius=12)
                card.pack(fill="x", padx=10, pady=5)
                
                img_ctk = cargar_imagen_ctk(pub.producto_ofrecido.imagen_path, size=(60, 60))
                lbl_img = ctk.CTkLabel(card, image=img_ctk, text="")
                lbl_img.pack(side="left", padx=15, pady=10)
                
                info = ctk.CTkLabel(
                    card, text=f"Ofreces: {pub.producto_ofrecido.titulo}\nBuscas a cambio: {pub.producto_buscado}\nDetalle: {pub.descripcion_busqueda}",
                    justify="left", font=ctk.CTkFont(size=12)
                )
                info.pack(side="left", padx=10, pady=10)
                
                btn_cancelar = ctk.CTkButton(
                    card, text="Cancelar Trueque", fg_color="#5c1d1d", hover_color="#ef4444",
                    text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=120, height=28,
                    command=lambda p=pub: self.cancelar_trueque(p)
                )
                btn_cancelar.pack(side="right", padx=15, pady=10)
                
        # --- 3.3. MIS EMPEÑOS ACTIVOS ---
        ctk.CTkLabel(f, text="💰 Mis Empeños y Préstamos Activos", font=ctk.CTkFont(size=16, weight="bold"), text_color="#a855f7").pack(anchor="w", padx=10, pady=(20, 5))
        
        # Empeños tomados (Yo pedí prestado)
        empenios_tomados = [p for p in self.sistema.publicaciones_empenio if p.duenio == usuario and p.activa]
        if empenios_tomados:
            ctk.CTkLabel(f, text="Prendas empeñadas (Pediste dinero prestado):", font=ctk.CTkFont(size=12, weight="bold"), text_color="#cca152").pack(anchor="w", padx=15, pady=(5, 2))
            for pub in empenios_tomados:
                card = ctk.CTkFrame(f, fg_color="#18181b", border_width=1, border_color="#a855f7", corner_radius=12)
                card.pack(fill="x", padx=10, pady=5)
                
                img_ctk = cargar_imagen_ctk(pub.producto.imagen_path, size=(60, 60))
                lbl_img = ctk.CTkLabel(card, image=img_ctk, text="")
                lbl_img.pack(side="left", padx=15, pady=10)
                
                prestamista_nombre = pub.modalidad.prestamista.nombre if pub.modalidad.prestamista else "Nadie financió aún"
                capital = pub.modalidad.monto_prestamo
                interes = capital * (pub.modalidad.tasa_interes / 100.0)
                total_a_pagar = capital + interes
                
                desc_text = f"Prenda: {pub.producto.titulo}\nPréstamo: ${capital:,.2f} (Plazo: {pub.modalidad.plazo_dias} días)  •  Prestamista: {prestamista_nombre}\nEstado: {pub.modalidad.estado}  •  Monto para recuperar: ${total_a_pagar:,.2f} (+{pub.modalidad.tasa_interes}% interés)"
                info = ctk.CTkLabel(card, text=desc_text, justify="left", font=ctk.CTkFont(size=12))
                info.pack(side="left", padx=10, pady=10)
                
                if pub.modalidad.estado == "Activo":
                    btn_pagar = ctk.CTkButton(
                        card, text="Pagar Deuda", fg_color="#10b981", hover_color="#059669",
                        text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=120, height=28,
                        command=lambda p=pub: self.pagar_empenio_deuda(p)
                    )
                    btn_pagar.pack(side="right", padx=15, pady=10)
                elif pub.modalidad.estado == "Pendiente":
                    btn_cancelar = ctk.CTkButton(
                        card, text="Cancelar Empeño", fg_color="#5c1d1d", hover_color="#ef4444",
                        text_color="#ffffff", font=ctk.CTkFont(size=11, weight="bold"), width=120, height=28,
                        command=lambda p=pub: self.cancelar_publicacion_empenio(p)
                    )
                    btn_cancelar.pack(side="right", padx=15, pady=10)
        else:
            ctk.CTkLabel(f, text="No tenés prendas empeñadas activas.", font=ctk.CTkFont(size=12, slant="italic"), text_color="#71717a").pack(anchor="w", padx=25, pady=5)
            
    def cancelar_publicacion_venta(self, pub):
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de cancelar la venta de '{pub.producto.titulo}'?"):
            pub.activa = False
            if pub in self.sistema.publicaciones_inicio:
                self.sistema.publicaciones_inicio.remove(pub)
            if pub in self.sistema.publicaciones_venta:
                self.sistema.publicaciones_venta.remove(pub)
            
            # Notificar e historial
            usuario = self.sistema.usuario_logueado
            usuario.registrar_actividad(f"Ventas: Cancelaste la publicación de venta del producto '{pub.producto.titulo}'")
            notificar(usuario, f"Cancelaste la venta de '{pub.producto.titulo}'.", "info")
            self.actualizar_actividades()
            if self.callback_actualizar_combos:
                self.callback_actualizar_combos()
                
    def cancelar_publicacion_empenio(self, pub):
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de cancelar el empeño de '{pub.producto.titulo}'?"):
            pub.activa = False
            if pub in self.sistema.publicaciones_inicio:
                self.sistema.publicaciones_inicio.remove(pub)
            if pub in self.sistema.publicaciones_empenio:
                self.sistema.publicaciones_empenio.remove(pub)
            
            # Notificar e historial
            usuario = self.sistema.usuario_logueado
            usuario.registrar_actividad(f"Empeños: Cancelaste el pedido de empeño de '{pub.producto.titulo}'")
            notificar(usuario, f"Cancelaste el empeño de '{pub.producto.titulo}'.", "info")
            self.actualizar_actividades()
            if self.callback_actualizar_combos:
                self.callback_actualizar_combos()
                
    def cancelar_trueque(self, pub):
        if messagebox.askyesno("Confirmar", f"¿Estás seguro de cancelar el trueque de '{pub.producto_ofrecido.titulo}'?"):
            if pub in self.sistema.publicaciones_trueque:
                self.sistema.publicaciones_trueque.remove(pub)
            if pub in self.sistema.publicaciones_inicio:
                self.sistema.publicaciones_inicio.remove(pub)
            
            # Notificar e historial
            usuario = self.sistema.usuario_logueado
            usuario.registrar_actividad(f"Trueques: Cancelaste el trueque por '{pub.producto_buscado}'")
            notificar(usuario, "Trueque cancelado.", "info")
            self.actualizar_actividades()
            if self.callback_actualizar_combos:
                self.callback_actualizar_combos()
                
    def aceptar_oferta(self, publicacion, usuario_ganador):
        try:
            monto = publicacion.modalidad.ofertas[usuario_ganador]
            # Ejecutar intercambio
            publicacion.seleccionar_ganador(usuario_ganador)
            
            # Quitar de publicaciones del mercado de inicio
            if publicacion in self.sistema.publicaciones_inicio:
                self.sistema.publicaciones_inicio.remove(publicacion)
                
            # Notificar al ganador
            notificar(usuario_ganador, f"¡Tu oferta por '{publicacion.producto.titulo}' fue aceptada! Pagaste ${monto:,.2f}.", "exito")
            
            from vista_comprobante import VistaComprobante
            VistaComprobante(self.winfo_toplevel(), publicacion, usuario_ganador)
            
            # Refrescar
            self.actualizar_actividades()
            if self.callback_actualizar_combos:
                self.callback_actualizar_combos()
                
        except ValueError as error:
            messagebox.showerror("Error al concretar", str(error))
            
    def rechazar_oferta(self, oferta):
        oferta.rechazar()
        # Notificar al comprador
        notificar(oferta.comprador, f"Tu oferta de ${oferta.monto:,.2f} por el producto '{oferta.comprador.productos_propios[0].titulo if oferta.comprador.productos_propios else ''}' fue rechazada.", "error")
        self.actualizar_actividades()
        
    def pagar_empenio_deuda(self, pub):
        usuario = self.sistema.usuario_logueado
        if not usuario:
            return
            
        capital = pub.modalidad.monto_prestamo
        interes = capital * (pub.modalidad.tasa_interes / 100.0)
        total_pago = capital + interes
        
        if usuario.saldo < total_pago:
            messagebox.showerror("Saldo insuficiente", f"No tenés saldo suficiente para pagar la deuda de ${total_pago:,.2f} (Saldo actual: ${usuario.saldo:,.2f}).")
            return
            
        if messagebox.askyesno("Confirmar Pago", f"¿Deseas pagar ${total_pago:,.2f} para recuperar tu '{pub.producto.titulo}'?"):
            prestamista = pub.modalidad.prestamista
            
            # Transferencias de saldo
            usuario.modificar_saldo(-total_pago)
            prestamista.modificar_saldo(total_pago)
            
            # Devolver el producto al dueño original
            prestamista.remover_producto(pub.producto)
            usuario.agregar_producto(pub.producto)
            
            # Cambiar estado
            pub.modalidad.estado = "Devuelto"
            pub.activa = False
            
            if pub in self.sistema.publicaciones_empenio:
                self.sistema.publicaciones_empenio.remove(pub)
                
            # Historial
            usuario.registrar_actividad(f"Empeño: Recuperaste {pub.producto.titulo} pagando ${total_pago:,.2f} de deuda a {prestamista.nombre}")
            prestamista.registrar_actividad(f"Préstamo: Cobraste ${total_pago:,.2f} de préstamo devuelto por {usuario.nombre} ({pub.producto.titulo} regresado)")
            
            # Notificar
            notificar(usuario, f"¡Recuperaste tu '{pub.producto.titulo}'! Deuda saldada por ${total_pago:,.2f}.", "exito")
            notificar(prestamista, f"¡Cobraste un préstamo! {usuario.nombre} te pagó ${total_pago:,.2f} por su '{pub.producto.titulo}'.", "exito")
            
            self.actualizar_actividades()
            if self.callback_actualizar_combos:
                self.callback_actualizar_combos()

    # =====================================================================
    # 4. PESTAÑA: HISTORIAL COMPLETO
    # =====================================================================
    def crear_tab_historial(self):
        f = ctk.CTkFrame(self.contenedor_pestania, fg_color="transparent")
        self.frames_pestanias["Historial"] = f
        
        ctk.CTkLabel(
            f, text="📜 Historial de Actividades del Coleccionista", 
            font=ctk.CTkFont(weight="bold", size=15), text_color="#cca152"
        ).pack(anchor="w", padx=5, pady=(0, 10))
        
        self.scroll_historial = ctk.CTkScrollableFrame(f, fg_color="#111116", border_width=1, border_color="#27272a", corner_radius=14)
        self.scroll_historial.pack(fill="both", expand=True)
        
    def actualizar_historial(self):
        for widget in self.scroll_historial.winfo_children():
            widget.destroy()
            
        usuario = self.sistema.usuario_logueado
        if not usuario or not usuario.actividades:
            ctk.CTkLabel(
                self.scroll_historial, text="No hay registros en el historial.", 
                text_color="#71717a", font=ctk.CTkFont(slant="italic")
            ).pack(pady=40)
            return
            
        # Mostrar actividades de la más nueva a la más antigua
        for act in reversed(usuario.actividades):
            card = ctk.CTkFrame(self.scroll_historial, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=8)
            card.pack(fill="x", pady=4, padx=5)
            
            ctk.CTkLabel(
                card, text=act, font=ctk.CTkFont(size=12), text_color="#f8fafc", 
                justify="left", anchor="w"
            ).pack(fill="x", padx=12, pady=10)
