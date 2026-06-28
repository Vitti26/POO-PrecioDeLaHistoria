# main.py
import sys
import os

# Agregar la carpeta 'interfaces' al path de Python para resolver importaciones
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "interfaces"))

from backend import SistemaPlataforma
# pyrefly: ignore [missing-import]
from vista_login import VistaLogin

def iniciar_app():
    # 1. Instanciamos el controlador del Backend
    sistema = SistemaPlataforma()
    
    # 2. Forzamos el flujo de control para que comience deslogueado
    sistema.usuario_logueado = None 

    # 3. Lanzamos la ventana de Login nativa
    app_login = VistaLogin(sistema)
    app_login.mainloop()

if __name__ == "__main__":
    iniciar_app()