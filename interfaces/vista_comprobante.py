# vista_comprobante.py
import os
import datetime
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

class VistaComprobante(ctk.CTkToplevel):
    def __init__(self, parent, publicacion, contraparte):
        super().__init__(parent)
        self.publicacion = publicacion
        self.contraparte = contraparte
        self.producto = publicacion.producto
        self.modalidad = publicacion.modalidad
        
        self.title("Comprobante de Operación")
        self.geometry("450x620")
        self.resizable(False, False)
        self.configure(fg_color="#09090b") # Fondo oscuro premium
        
        # Generar metadatos únicos para el comprobante
        self.nro_factura = f"FAC-{datetime.datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        self.fecha_emision = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Hacer ventana modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar ventana con respecto al padre
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self.armar_ui()

    def armar_ui(self):
        # Frame del recibo (aspecto papel/ticket digital)
        recibo_frame = ctk.CTkFrame(self, fg_color="#18181b", border_width=1, border_color="#cca152", corner_radius=15)
        recibo_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Encabezado (Logo de la app)
        ctk.CTkLabel(
            recibo_frame, 
            text="EL PRECIO DE LA HISTORIA", 
            font=ctk.CTkFont("Georgia", 16, "bold"), 
            text_color="#cca152"
        ).pack(pady=(20, 2))
        
        ctk.CTkLabel(
            recibo_frame, 
            text="Comprobante Electrónico Oficial", 
            font=ctk.CTkFont(size=10, slant="italic"), 
            text_color="#71717a"
        ).pack()
        
        # Separador superior
        self.dibujar_linea_punteada(recibo_frame)
        
        # Información General de la Factura
        info_gral_frame = ctk.CTkFrame(recibo_frame, fg_color="transparent")
        info_gral_frame.pack(fill="x", padx=20, pady=5)
        
        self.agregar_fila_detalle(info_gral_frame, "Factura Nro:", self.nro_factura, valor_color="#cca152")
        self.agregar_fila_detalle(info_gral_frame, "Fecha/Hora:", self.fecha_emision)
        
        # Determinar tipo de operación
        if self.publicacion.tipo == "Venta":
            tipo_transaccion = "Compraventa Directa"
            vendedor = self.publicacion.duenio.nombre
            comprador = self.contraparte.nombre
            self.agregar_fila_detalle(info_gral_frame, "Tipo Operación:", tipo_transaccion)
            self.agregar_fila_detalle(info_gral_frame, "Vendedor:", vendedor)
            self.agregar_fila_detalle(info_gral_frame, "Comprador:", comprador)
        else: # Empeño
            tipo_transaccion = "Préstamo Prendario con Garantía"
            prestatario = self.publicacion.duenio.nombre # Dueño original que pide el dinero
            prestamista = self.contraparte.nombre # Financista que presta el dinero
            self.agregar_fila_detalle(info_gral_frame, "Tipo Operación:", tipo_transaccion)
            self.agregar_fila_detalle(info_gral_frame, "Prestatario (Deudor):", prestatario)
            self.agregar_fila_detalle(info_gral_frame, "Prestamista (Acreedor):", prestamista)
            
        # Separador del cuerpo
        self.dibujar_linea_punteada(recibo_frame)
        
        # Detalle del Objeto
        ctk.CTkLabel(
            recibo_frame, 
            text="DETALLE DEL ARTÍCULO", 
            font=ctk.CTkFont(size=11, weight="bold"), 
            text_color="#cca152"
        ).pack(anchor="w", padx=20, pady=(5, 5))
        
        prod_frame = ctk.CTkFrame(recibo_frame, fg_color="#27272a", corner_radius=8)
        prod_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(
            prod_frame, 
            text=self.producto.titulo, 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="white"
        ).pack(anchor="w", padx=12, pady=(8, 2))
        
        desc = self.producto.descripcion
        if len(desc) > 80:
            desc = desc[:77] + "..."
        ctk.CTkLabel(
            prod_frame, 
            text=desc, 
            font=ctk.CTkFont(size=10), 
            text_color="#a0a0a5", 
            wraplength=350, 
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))
        
        # Separador de precios
        self.dibujar_linea_punteada(recibo_frame)
        
        # Desglose Financiero
        precios_frame = ctk.CTkFrame(recibo_frame, fg_color="transparent")
        precios_frame.pack(fill="x", padx=20, pady=5)
        
        if self.publicacion.tipo == "Venta":
            # Si es venta
            monto_neto = self.modalidad.monto_pagado
            comision_plataforma = monto_neto * 0.05  # Ficticio 5% de tarifa de servicio
            total_operacion = monto_neto
            
            # Intentar obtener medio de pago de los registros de pago
            medio_pago = "Transferencia / Saldo Plataforma"
            if self.contraparte in self.modalidad.pagos:
                medio_pago = self.modalidad.pagos[self.contraparte].medio
                
            self.agregar_fila_detalle(precios_frame, "Valor de Venta:", f"${monto_neto:,.2f}")
            self.agregar_fila_detalle(precios_frame, "Medio de Pago:", medio_pago)
            self.agregar_fila_detalle(precios_frame, "Tasa de Servicio (5% incl.):", f"${comision_plataforma:,.2f}", valor_color="#a0a0a5")
            
            self.dibujar_linea_punteada(recibo_frame)
            
            # Total Grande
            total_frame = ctk.CTkFrame(recibo_frame, fg_color="transparent")
            total_frame.pack(fill="x", padx=20, pady=5)
            self.agregar_fila_detalle(total_frame, "TOTAL PAGADO:", f"${total_operacion:,.2f}", label_font=ctk.CTkFont(size=14, weight="bold"), valor_font=ctk.CTkFont(size=16, weight="bold"), valor_color="#cca152")
            
        else: # Empeño
            capital = self.modalidad.monto_prestamo
            tasa = self.modalidad.tasa_interes
            plazo = self.modalidad.plazo_dias
            interes_monto = capital * (tasa / 100)
            total_retorno = capital + interes_monto
            
            # Calcular fecha de vencimiento estimada
            vencimiento = (datetime.datetime.now() + datetime.timedelta(days=plazo)).strftime("%d/%m/%Y")
            
            self.agregar_fila_detalle(precios_frame, "Monto Prestado (Capital):", f"${capital:,.2f}")
            self.agregar_fila_detalle(precios_frame, "Plazo Pactado:", f"{plazo} días")
            self.agregar_fila_detalle(precios_frame, "Tasa de Interés:", f"{tasa}%")
            self.agregar_fila_detalle(precios_frame, "Costo de Financiación (Interés):", f"${interes_monto:,.2f}", valor_color="#a0a0a5")
            self.agregar_fila_detalle(precios_frame, "Fecha Límite Devolución:", vencimiento)
            
            self.dibujar_linea_punteada(recibo_frame)
            
            # Total Grande
            total_frame = ctk.CTkFrame(recibo_frame, fg_color="transparent")
            total_frame.pack(fill="x", padx=20, pady=5)
            self.agregar_fila_detalle(total_frame, "TOTAL A REEMBOLSAR:", f"${total_retorno:,.2f}", label_font=ctk.CTkFont(size=14, weight="bold"), valor_font=ctk.CTkFont(size=16, weight="bold"), valor_color="#cca152")
            
        # Botones de Acción abajo
        btn_frame = ctk.CTkFrame(recibo_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        
        # Botón Guardar en Disco
        btn_guardar = ctk.CTkButton(
            btn_frame, 
            text="📥 Guardar Comprobante", 
            fg_color="#cca152", 
            text_color="#000000", 
            hover_color="#b58c42",
            font=ctk.CTkFont(weight="bold"),
            height=36,
            command=self.guardar_comprobante_archivo
        )
        btn_guardar.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Botón Cerrar
        btn_cerrar = ctk.CTkButton(
            btn_frame, 
            text="Entendido", 
            fg_color="#27272a", 
            text_color="white", 
            hover_color="#3f3f46",
            height=36,
            command=self.destroy
        )
        btn_cerrar.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def dibujar_linea_punteada(self, parent):
        lbl = ctk.CTkLabel(
            parent, 
            text="----------------- • -----------------", 
            font=ctk.CTkFont(size=12, weight="bold"), 
            text_color="#3f3f46"
        )
        lbl.pack(pady=8)

    def agregar_fila_detalle(self, parent, label_text, valor_text, label_font=None, valor_font=None, valor_color="white"):
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", pady=2)
        
        lf = label_font or ctk.CTkFont(size=11)
        vf = valor_font or ctk.CTkFont(size=11)
        
        ctk.CTkLabel(fila, text=label_text, font=lf, text_color="#a0a0a5").pack(side="left")
        ctk.CTkLabel(fila, text=valor_text, font=vf, text_color=valor_color).pack(side="right")

    def generar_texto_comprobante(self):
        # Armar string de texto plano estructurado como factura
        separador = "=" * 50
        linea_simple = "-" * 50
        
        texto = []
        texto.append(separador)
        texto.append("           EL PRECIO DE LA HISTORIA")
        texto.append("        Comprobante de Operación Digital")
        texto.append(separador)
        texto.append(f"Factura Nro:       {self.nro_factura}")
        texto.append(f"Fecha Emisión:     {self.fecha_emision}")
        texto.append(linea_simple)
        
        if self.publicacion.tipo == "Venta":
            medio_pago = "Transferencia / Saldo Plataforma"
            if self.contraparte in self.modalidad.pagos:
                medio_pago = self.modalidad.pagos[self.contraparte].medio
            monto_neto = self.modalidad.monto_pagado
            comision = monto_neto * 0.05
            
            texto.append(f"Tipo Transacción:  Compraventa Directa")
            texto.append(f"Vendedor:          {self.publicacion.duenio.nombre}")
            texto.append(f"Comprador:         {self.contraparte.nombre}")
            texto.append(linea_simple)
            texto.append(f"Artículo:          {self.producto.titulo}")
            texto.append(f"Descripción:       {self.producto.descripcion}")
            texto.append(linea_simple)
            texto.append(f"Subtotal:          ${monto_neto:,.2f}")
            texto.append(f"Medio de Pago:     {medio_pago}")
            texto.append(f"Tasa Plataforma:   ${comision:,.2f} (incl.)")
            texto.append(linea_simple)
            texto.append(f"TOTAL PAGADO:      ${monto_neto:,.2f}")
        else: # Empeño
            capital = self.modalidad.monto_prestamo
            tasa = self.modalidad.tasa_interes
            plazo = self.modalidad.plazo_dias
            interes_monto = capital * (tasa / 100)
            total_retorno = capital + interes_monto
            vencimiento = (datetime.datetime.now() + datetime.timedelta(days=plazo)).strftime("%d/%m/%Y")
            
            texto.append(f"Tipo Transacción:  Préstamo Prendario (Empeño)")
            texto.append(f"Prestatario:       {self.publicacion.duenio.nombre}")
            texto.append(f"Prestamista:       {self.contraparte.nombre}")
            texto.append(linea_simple)
            texto.append(f"Artículo en Garantía: {self.producto.titulo}")
            texto.append(linea_simple)
            texto.append(f"Capital Prestado:  ${capital:,.2f}")
            texto.append(f"Plazo Pactado:     {plazo} días")
            texto.append(f"Tasa Interés:      {tasa}%")
            texto.append(f"Intereses Totales: ${interes_monto:,.2f}")
            texto.append(f"Vencimiento Pago:  {vencimiento}")
            texto.append(linea_simple)
            texto.append(f"TOTAL A REEMBOLSAR: ${total_retorno:,.2f}")
            
        texto.append(separador)
        texto.append(" Gracias por operar en El Precio de la Historia.")
        texto.append(separador)
        
        return "\n".join(texto)

    def guardar_comprobante_archivo(self):
        # Abrir diálogo para guardar archivo
        tipo_nombre = "venta" if self.publicacion.tipo == "Venta" else "empenio"
        default_filename = f"comprobante_{tipo_nombre}_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        
        file_path = filedialog.asksaveasfilename(
            title="Guardar Factura / Comprobante",
            defaultextension=".txt",
            filetypes=[("Archivos de Texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialfile=default_filename
        )
        
        if file_path:
            try:
                contenido = self.generar_texto_comprobante()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(contenido)
                messagebox.showinfo("Éxito", f"Comprobante guardado correctamente en:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
