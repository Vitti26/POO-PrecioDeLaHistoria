# vista_login.py
import customtkinter as ctk
from tkinter import messagebox
from frontend import AppElPrecioDeLaHistoria

class VistaLogin(ctk.CTk):
    def __init__(self, sistema):
        super().__init__()
        self.sistema = sistema
        self.title("Acceso - El Precio de la Historia")
        self.geometry("450x550")
        self.resizable(False, False)
        self.configure(fg_color="#09090b") # Fondo oscuro premium
        
        self.armar_ui()

    def armar_ui(self):
        # Contenedor central con borde sutil
        self.frame_login = ctk.CTkFrame(self, fg_color="#18181b", border_width=1, border_color="#27272a", corner_radius=15)
        self.frame_login.pack(expand=True, padx=40, pady=40, fill="both")

        # Logo / Título
        ctk.CTkLabel(self.frame_login, text="EL PRECIO\nDE LA HISTORIA", font=ctk.CTkFont("Georgia", 24, "bold"), text_color="#cca152").pack(pady=(40, 10))
        ctk.CTkLabel(self.frame_login, text="Iniciá sesión para continuar", font=ctk.CTkFont(size=14), text_color="#a0a0a5").pack(pady=(0, 30))

        # Entradas de texto
        self.entry_usuario = ctk.CTkEntry(self.frame_login, placeholder_text="Usuario (Ej: Marcos)", height=45, fg_color="#27272a", border_width=0)
        self.entry_usuario.pack(fill="x", padx=30, pady=10)

        self.entry_password = ctk.CTkEntry(self.frame_login, placeholder_text="Contraseña", height=45, fg_color="#27272a", border_width=0, show="•")
        self.entry_password.pack(fill="x", padx=30, pady=10)

        # Botón de Ingreso
        btn_ingresar = ctk.CTkButton(
            self.frame_login, text="Ingresar", height=45, font=ctk.CTkFont(weight="bold", size=14),
            fg_color="#cca152", text_color="#000000", hover_color="#b58c42",
            command=self.validar_ingreso
        )
        btn_ingresar.pack(fill="x", padx=30, pady=(30, 10))

        # Botón de registro simulado
        ctk.CTkButton(
            self.frame_login, text="¿No tenés cuenta? Registrate", fg_color="transparent", 
            text_color="#3b82f6", hover_color="#27272a", width=260, command=self.simular_registro
        ).pack(pady=5)

    def validar_ingreso(self):
        usuario = self.entry_usuario.get().strip()
        password = self.entry_password.get().strip()

        if not usuario or not password:
            messagebox.showwarning("Atención", "Completá usuario y contraseña.")
            return

        try:
            self.sistema.cargar_db()
        except Exception as e:
            print(f"Error cargando DB al validar ingreso: {e}")

        usuario_obj = next((u for u in self.sistema.usuarios.values() if u.nombre.lower() == usuario.lower()), None)

        if usuario_obj:
            if not usuario_obj.verificar_password(password):
                messagebox.showerror("Error", "Contraseña incorrecta.")
                return
                
            # Login exitoso
            self.sistema.usuario_logueado = usuario_obj
            self.destroy() # Destruimos la ventana de login
            
            # Lanzamos la app principal
            app = AppElPrecioDeLaHistoria(self.sistema)
            app.mainloop()
        else:
            messagebox.showerror("Error", "Usuario no encontrado. Probá con 'Marcos' (clave: 1234) o registrate.")

    def simular_registro(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Registro de Coleccionista")
        dialog.geometry("380x300")
        dialog.resizable(False, False)
        dialog.configure(fg_color="#09090b")
        dialog.transient(self)
        dialog.grab_set()

        # Centrar
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(dialog, text="CREAR NUEVA CUENTA", font=ctk.CTkFont("Georgia", 18, "bold"), text_color="#cca152").pack(pady=20)

        # Usuario
        ctk.CTkLabel(dialog, text="Nombre de Usuario:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=35)
        ent_nombre = ctk.CTkEntry(dialog, placeholder_text="Ej: Juan", border_color="#27272a", fg_color="#18181b", height=35)
        ent_nombre.pack(fill="x", padx=35, pady=(2, 12))

        # Contraseña
        ctk.CTkLabel(dialog, text="Contraseña (mínimo 4 caracteres):", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=35)
        ent_password = ctk.CTkEntry(dialog, placeholder_text="Contraseña", border_color="#27272a", fg_color="#18181b", height=35, show="•")
        ent_password.pack(fill="x", padx=35, pady=(2, 20))

        def registrar():
            nombre = ent_nombre.get().strip()
            password = ent_password.get().strip()
            saldo = 0.0

            if not nombre or not password:
                messagebox.showerror("Error", "Completá todos los campos.", parent=dialog)
                return
            if len(password) < 4:
                messagebox.showerror("Error", "La contraseña debe tener al menos 4 caracteres.", parent=dialog)
                return

            try:
                self.sistema.registrar_usuario(nombre, password, saldo)
                messagebox.showinfo("Éxito", f"¡Cuenta '{nombre}' registrada! Ya podés ingresar.", parent=dialog)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e), parent=dialog)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=35)

        ctk.CTkButton(
            btn_frame, text="Registrarse", fg_color="#cca152", text_color="#000000", hover_color="#b58c42",
            font=ctk.CTkFont(weight="bold"), height=35, command=registrar
        ).pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkButton(
            btn_frame, text="Cancelar", fg_color="#27272a", text_color="#ffffff", hover_color="#3f3f46",
            height=35, command=dialog.destroy
        ).pack(side="right", expand=True, fill="x", padx=(5, 0))