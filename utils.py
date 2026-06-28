# utils.py
import os
from PIL import Image
import customtkinter as ctk
_imagen_cache = {}

def cargar_imagen_ctk(ruta, size=(120, 120)):
    """
    Carga una imagen desde el disco y la retorna en formato CTkImage.
    Si la ruta es inválida, no existe o falla, retorna la imagen placeholder.
    Usa una caché para evitar accesos repetidos a disco o intentos fallidos de lectura.
    """
    cache_key = (ruta, size)
    if cache_key in _imagen_cache:
        return _imagen_cache[cache_key]

    placeholder_path = os.path.join("assets", "images", "placeholder.png")
    if not os.path.exists(placeholder_path):
        placeholder_path = os.path.join("..", "assets", "images", "placeholder.png")
    if not os.path.exists(placeholder_path):
        dir_of_utils = os.path.dirname(os.path.abspath(__file__))
        placeholder_path = os.path.join(os.path.dirname(dir_of_utils), "assets", "images", "placeholder.png")
    
    # Determinar ruta a cargar
    target_path = ruta
    if not target_path or not os.path.exists(target_path):
        target_path = placeholder_path
        
    try:
        if os.path.exists(target_path):
            pil_img = Image.open(target_path)
            res = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
            _imagen_cache[cache_key] = res
            return res
    except Exception as e:
        print(f"Error cargando imagen {target_path}: {e}")
        
    # Fallback al placeholder si no se intentó ya
    if target_path != placeholder_path:
        try:
            if os.path.exists(placeholder_path):
                pil_img = Image.open(placeholder_path)
                res = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
                _imagen_cache[cache_key] = res
                return res
        except Exception as ex:
            print(f"Fallo crítico cargando placeholder: {ex}")
            
    # Guardar None en caché para no reintentar
    _imagen_cache[cache_key] = None
    return None

# Registro global de la aplicación para interactuar con la UI si es necesario
_app_instancia = None

def registrar_app_global(app):
    global _app_instancia
    _app_instancia = app

def notificar(usuario, mensaje, tipo="info"):
    """
    Función unificada y global que puede ser llamada desde cualquier parte del proyecto
    para registrar una notificación y opcionalmente mostrarla en la interfaz.
    """
    if usuario:
        usuario.agregar_notificacion(mensaje, tipo)

def formatear_reputacion(valor):
    """
    Toma un valor de reputación de 0 a 5 y devuelve una representación premium
    en estrellas de caracteres Unicode (ej: ⭐⭐⭐⭐☆ 4.8).
    """
    if valor is None:
        return "Sin calificaciones"
    entero = int(round(valor))
    # Limitar entero entre 0 y 5
    entero = max(0, min(5, entero))
    estrellas_llenas = "★" * entero
    estrellas_vacias = "☆" * (5 - entero)
    return f"{estrellas_llenas}{estrellas_vacias} {valor:.1f}"


def aplicar_hover_premium(card, color_acento, original_border="#27272a"):
    """
    Aplica un efecto de hover premium a un frame de CustomTkinter, cambiando
    su color de fondo y borde de manera coordinada. Además, enlaza el evento
    recursivamente a todos los elementos internos para evitar parpadeos.
    """
    original_fg = card.cget("fg_color")
    # Si el fondo original es oscuro, usamos un color de hover premium
    if original_fg in ["#18181b", "#15151a", "#111116", "#09090b"]:
        hover_fg = "#202028"
    else:
        hover_fg = "#2a2a35"

    def on_enter(e):
        card.configure(border_color=color_acento, fg_color=hover_fg)

    def on_leave(e):
        card.configure(border_color=original_border, fg_color=original_fg)

    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)

    def bind_children(widget):
        for child in widget.winfo_children():
            # No sobreescribir eventos de widgets interactivos estándar
            if not isinstance(child, (ctk.CTkButton, ctk.CTkComboBox, ctk.CTkEntry)):
                child.bind("<Enter>", on_enter)
                child.bind("<Leave>", on_leave)
                # También propagar cursor hand2 para que se sienta clickeable
                if card.cget("cursor") == "hand2":
                    child.configure(cursor="hand2")
                bind_children(child)

    bind_children(card)



