# vista_faq.py
import customtkinter as ctk

class VistaFAQ(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Título
        ctk.CTkLabel(
            self, text="❓ CENTRO DE AYUDA Y FAQ", 
            font=ctk.CTkFont(size=22, weight="bold"), text_color="#3b82f6"
        ).pack(anchor="w", pady=(10, 20))
        
        # Scrollable Frame para las preguntas
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self.armar_preguntas()

    def armar_preguntas(self):
        preguntas = [
            ("¿Cómo publico un artículo para trueque?", "Andá a la pestaña 'Trueques' y usá el formulario de la izquierda. Seleccioná el ítem de tu inventario que querés ofrecer, y escribí qué estás buscando a cambio. ¡Listo, tu publicación irá a la cartelera!"),
            ("¿Es seguro realizar empeños acá?", "Sí. Al financiar un empeño, el artículo prendado pasa temporalmente a tu inventario como garantía. Si el deudor no devuelve el dinero en el plazo acordado, te quedás con el producto definitivamente."),
            ("¿Cómo cargo saldo en mi cuenta?", "Dirigite a 'Mi Cuenta' > 'Billetera y Banco'. Vinculá tu CBU o Alias y simulá la carga de saldo. Se acreditará instantáneamente para que puedas comprar o financiar empeños."),
            ("¿Por qué mi reputación dice 'Sin calificaciones'?", "La reputación se construye a medida que cerrás tratos exitosos. Una vez concretada una venta o un trueque, el sistema te asignará estrellas basadas en tu historial."),
            ("¿Puedo deshacer un trueque ya aceptado?", "No. Las transacciones son finales y los objetos cambian de dueño automáticamente en el motor de la plataforma mediante Programación Orientada a Objetos.")
        ]

        for pre, resp in preguntas:
            card = ctk.CTkFrame(self.scroll, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=10)
            card.pack(fill="x", pady=8, padx=5)
            
            ctk.CTkLabel(card, text=f"💬 {pre}", font=ctk.CTkFont(size=14, weight="bold"), text_color="#cca152", justify="left").pack(anchor="w", padx=15, pady=(15, 5))
            ctk.CTkLabel(card, text=resp, font=ctk.CTkFont(size=13), text_color="#a0a0a5", justify="left", wraplength=700).pack(anchor="w", padx=15, pady=(0, 15))