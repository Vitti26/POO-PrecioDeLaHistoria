# backend.py
import datetime
from abc import ABC, abstractmethod
import json
import os
import time
import urllib.request
import urllib.error


class ObservableList(list):
    def __init__(self, iterable=None, callback=None):
        if iterable is not None:
            super().__init__(iterable)
        else:
            super().__init__()
        self.callback = callback

    def append(self, item):
        super().append(item)
        if self.callback:
            self.callback()

    def remove(self, item):
        super().remove(item)
        if self.callback:
            self.callback()

    def clear(self):
        super().clear()
        if self.callback:
            self.callback()

    def pop(self, index=-1):
        item = super().pop(index)
        if self.callback:
            self.callback()
        return item

    def extend(self, iterable):
        super().extend(iterable)
        if self.callback:
            self.callback()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self.callback:
            self.callback()

    def __delitem__(self, key):
        super().__delitem__(key)
        if self.callback:
            self.callback()

_save_hook = None

def auto_save():
    if _save_hook:
        _save_hook()


def _firebase_http(url, method="GET", data=None):
    try:
        json_data = None
        if data is not None:
            json_data = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=json_data, 
            headers={"Content-Type": "application/json"} if json_data else {}, 
            method=method
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"HTTPError en Firebase {method} {url}: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"Error de red/conexión con Firebase: {e}")
        return None




class Usuario:
    """
    Representa a un coleccionista de la plataforma.
    Encapsula su estado interno (saldo, reputación, productos, etc.) detrás
    de propiedades, evitando que el resto del sistema lo modifique sin pasar
    por las reglas de negocio (depositar_fondos, modificar_saldo, etc.).
    """

    def __init__(self, nombre: str, saldo_inicial: float = 0.0, password: str = "1234",
                 reputacion: float = 5.0, transacciones: int = 0, avatar_path: str = None):
        self._nombre = self._validar_nombre(nombre)
        self._password = password or "1234"
        self._saldo = max(0.0, saldo_inicial)
        self._reputacion = reputacion
        self._transacciones_completadas = transacciones
        self.avatar_path = avatar_path

        # Atributos de banco simulado
        self.banco_vinculado = False
        self.banco_nombre = ""
        self.cbu_alias = ""
        self.tarjeta_nro = ""

        self._productos_propios = ObservableList(callback=auto_save)
        self._notificaciones = ObservableList(callback=auto_save)
        self._actividades = ObservableList(callback=auto_save)
        self.app_callback = None

    # ------------------------------------------------------------------
    # Propiedades (encapsulamiento): el resto del sistema solo puede LEER
    # estos valores o modificarlos a través de métodos controlados.
    # ------------------------------------------------------------------
    @property
    def nombre(self):
        return self._nombre

    @nombre.setter
    def nombre(self, nuevo_nombre):
        self._nombre = self._validar_nombre(nuevo_nombre)
        auto_save()

    @staticmethod
    def _validar_nombre(nombre):
        if not nombre or not str(nombre).strip():
            raise ValueError("El nombre de usuario no puede estar vacío.")
        return str(nombre).strip()

    @property
    def saldo(self):
        return self._saldo

    @property
    def reputacion(self):
        return self._reputacion

    @property
    def transacciones_completadas(self):
        return self._transacciones_completadas

    @property
    def productos_propios(self):
        # Devolvemos una copia para que nadie pueda mutar la lista interna
        # desde afuera (rompería el encapsulamiento).
        return list(self._productos_propios)

    @property
    def notificaciones(self):
        return list(self._notificaciones)

    @property
    def actividades(self):
        return list(self._actividades)

    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------
    def verificar_password(self, password: str) -> bool:
        return self._password == password

    def cambiar_password(self, password_actual: str, password_nueva: str):
        if not self.verificar_password(password_actual):
            raise ValueError("La contraseña actual es incorrecta.")
        if not password_nueva or len(password_nueva) < 4:
            raise ValueError("La nueva contraseña debe tener al menos 4 caracteres.")
        self._password = password_nueva
        self.registrar_actividad("Seguridad: Cambiaste tu contraseña")

    # ------------------------------------------------------------------
    # Inventario
    # ------------------------------------------------------------------
    def agregar_producto(self, producto):
        if producto not in self._productos_propios:
            self._productos_propios.append(producto)
        producto._asignar_duenio(self)

    def remover_producto(self, producto):
        if producto in self._productos_propios:
            self._productos_propios.remove(producto)

    # ------------------------------------------------------------------
    # Finanzas
    # ------------------------------------------------------------------
    def modificar_saldo(self, monto: float):
        nuevo_saldo = self._saldo + monto
        if nuevo_saldo < 0:
            raise ValueError("La operación dejaría el saldo en negativo.")
        self._saldo = nuevo_saldo
        auto_save()

    def vincular_banco(self, banco_nombre: str, cbu_alias: str, tarjeta_nro: str, saldo_inicial: float):
        self.banco_nombre = banco_nombre
        self.cbu_alias = cbu_alias
        self.tarjeta_nro = tarjeta_nro
        self.banco_vinculado = True
        self.modificar_saldo(saldo_inicial)
        self.registrar_actividad(f"Banco: Vinculaste cuenta de {banco_nombre} (Alias: '{cbu_alias}') y acreditaste saldo inicial de ${saldo_inicial:,.2f}")

    def depositar_fondos(self, monto: float):
        if not self.banco_vinculado:
            raise ValueError("No tenés ninguna cuenta bancaria vinculada.")
        if monto <= 0:
            raise ValueError("El monto a depositar debe ser mayor a 0.")
        self.modificar_saldo(monto)
        self.registrar_actividad(f"Banco: Depósito de ${monto:,.2f} transferido desde cuenta de {self.banco_nombre}")

    # ------------------------------------------------------------------
    # Reputación y transacciones (solo el sistema las modifica)
    # ------------------------------------------------------------------
    def incrementar_transaccion(self):
        self._transacciones_completadas += 1
        auto_save()

    def actualizar_reputacion(self, nuevo_valor: float):
        self._reputacion = max(0.0, min(5.0, nuevo_valor))
        auto_save()

    # ------------------------------------------------------------------
    # Actividad y notificaciones
    # ------------------------------------------------------------------
    def registrar_actividad(self, descripcion: str):
        now_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        self._actividades.append(f"[{now_str}] {descripcion}")

    def agregar_notificacion(self, mensaje: str, tipo: str = "info"):
        now_str = datetime.datetime.now().strftime("%H:%M")
        notif = {
            "mensaje": mensaje,
            "tipo": tipo,
            "hora": now_str,
            "leida": False
        }
        self._notificaciones.append(notif)
        self.registrar_actividad(f"Notificación: {mensaje}")
        if self.app_callback:
            try:
                self.app_callback(notif)
            except Exception as e:
                print(f"Error en callback de notificación: {e}")

    def marcar_notificaciones_leidas(self):
        for n in self._notificaciones:
            n["leida"] = True
        auto_save()

    def limpiar_notificaciones(self):
        self._notificaciones.clear()

    def cantidad_no_leidas(self):
        return sum(1 for n in self._notificaciones if not n["leida"])

    def __str__(self):
        return f"Usuario: {self.nombre} (Productos: {len(self._productos_propios)})"

    def __eq__(self, other):
        if not isinstance(other, Usuario):
            return False
        return self.nombre.lower() == other.nombre.lower()

    def __hash__(self):
        return hash(self.nombre.lower())



class Producto:
    """
    Objeto coleccionable de un usuario. El dueño solo puede modificarse
    internamente a través de Usuario.agregar_producto/remover_producto,
    nunca asignando el atributo directamente desde afuera.
    """

    def __init__(self, titulo: str, descripcion: str, duenio: Usuario = None, imagen_path: str = None):
        self._titulo = self._validar_texto(titulo, "El título")
        self._descripcion = self._validar_texto(descripcion, "La descripción")
        self._duenio = None
        self.imagen_path = imagen_path
        if duenio:
            duenio.agregar_producto(self)

    @staticmethod
    def _validar_texto(valor, etiqueta):
        if not valor or not str(valor).strip():
            raise ValueError(f"{etiqueta} no puede estar vacía.")
        return str(valor).strip()

    @property
    def titulo(self):
        return self._titulo

    @titulo.setter
    def titulo(self, valor):
        self._titulo = self._validar_texto(valor, "El título")
        auto_save()

    @property
    def descripcion(self):
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor):
        self._descripcion = self._validar_texto(valor, "La descripción")
        auto_save()

    @property
    def duenio(self):
        return self._duenio

    def _asignar_duenio(self, nuevo_duenio: Usuario):
        """Método interno: solo Usuario.agregar_producto debe invocarlo."""
        self._duenio = nuevo_duenio

    def definir_imagen(self, ruta_origen: str):
        if not ruta_origen:
            self.imagen_path = None
            auto_save()
            return
        
        import os
        # Si ya es una ruta relativa en assets/images, no la volvemos a copiar
        if ruta_origen.startswith(os.path.join("assets", "images")):
            self.imagen_path = ruta_origen
            auto_save()
            return
            
        import shutil
        import uuid
        
        os.makedirs(os.path.join("assets", "images"), exist_ok=True)
        
        ext = os.path.splitext(ruta_origen)[1].lower()
        if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
            return
        
        nombre_archivo = f"{uuid.uuid4()}{ext}"
        ruta_destino = os.path.join("assets", "images", nombre_archivo)
        
        try:
            shutil.copy(ruta_origen, ruta_destino)
            self.imagen_path = ruta_destino
        except Exception as e:
            print(f"Error al copiar la imagen: {e}")
            self.imagen_path = None
        auto_save()

    def __str__(self):
        return f"[{self.titulo} - Dueño: {self.duenio.nombre if self.duenio else 'Nadie'}]"

    def __eq__(self, other):
        if not isinstance(other, Producto):
            return False
        self_duenio_nombre = self.duenio.nombre.lower() if self.duenio else None
        other_duenio_nombre = other.duenio.nombre.lower() if other.duenio else None
        return self.titulo.lower() == other.titulo.lower() and self_duenio_nombre == other_duenio_nombre

    def __hash__(self):
        duenio_nombre = self.duenio.nombre.lower() if self.duenio else None
        return hash((self.titulo.lower(), duenio_nombre))



class Modalidad(ABC):
    @abstractmethod
    def registrar_postulacion(self, publicacion, usuario_interesado, **kwargs):
        pass

    @abstractmethod
    def ejecutar_intercambio(self, publicacion, usuario_ganador):
        pass


class Pago:
    def __init__(self, monto: float, medio: str):
        self.monto = monto
        self.medio = medio
        self.estado = "Pendiente"
        
    def confirmar(self):
        self.estado = "Confirmado"


class Oferta:
    def __init__(self, comprador: Usuario, monto: float, medio_pago: str):
        self.comprador = comprador
        self.monto = monto
        self.medio_pago = medio_pago
        self.estado = "Pendiente"
        
    def aceptar(self):
        self.estado = "Aceptada"
        
    def rechazar(self):
        self.estado = "Rechazada"


class Venta(Modalidad):
    """
    Modalidad de intercambio por dinero. Además de la lógica de ofertas,
    soporta un circuito de devolución: el comprador puede solicitarla
    dentro de los 3 días de concretada la compra y el vendedor decide
    si la aprueba (revierte plata y producto) o la rechaza.
    """

    PLAZO_DEVOLUCION_DIAS = 3

    def __init__(self, precio_sugerido: float = 0.0, medio_pago_preferido: str = "Mercado Pago"):
        self.precio_sugerido = precio_sugerido
        self.medio_pago_preferido = medio_pago_preferido
        self.ofertas = {}  # usuario -> float
        self.pagos = {}    # usuario -> Pago
        self.ofertas_list = [] # lista de objetos Oferta

        # --- Estado de la compra concretada (para devoluciones) ---
        self.comprador_final = None
        self.vendedor_final = None
        self.monto_pagado = 0.0
        self.fecha_compra = None
        self.estado_devolucion = "N/A"  # N/A | Disponible | Solicitada | Aprobada | Rechazada
        self.motivo_devolucion = ""

    def registrar_postulacion(self, publicacion, usuario_interesado, **kwargs):
        monto = kwargs.get("monto")
        medio_pago = kwargs.get("medio_pago")
        
        if monto is None:
            raise ValueError("Tenés que indicar un monto.")
        if monto <= 0:
            raise ValueError("El monto tiene que ser mayor a 0.")
        if medio_pago is None:
            raise ValueError("Tenés que elegir un medio de pago.")
            
        nueva_oferta = Oferta(usuario_interesado, monto, medio_pago)
        self.ofertas_list.append(nueva_oferta)
        self.ofertas[usuario_interesado] = monto
        self.pagos[usuario_interesado] = Pago(monto, medio_pago)
        auto_save()
        
    def ejecutar_intercambio(self, publicacion, usuario_ganador):
        producto = publicacion.producto
        vendedor = publicacion.duenio
        
        if usuario_ganador not in self.ofertas:
            raise ValueError("El usuario elegido no hizo ninguna oferta.")
            
        monto = self.ofertas[usuario_ganador]
        pago = self.pagos[usuario_ganador]
        
        if usuario_ganador.saldo < monto:
            raise ValueError("El comprador no tiene saldo suficiente.")
            
        # Aceptar la ganadora y rechazar las demás
        for ofr in self.ofertas_list:
            if ofr.comprador == usuario_ganador:
                ofr.aceptar()
            else:
                ofr.rechazar()
                
        pago.confirmar()
        
        vendedor.modificar_saldo(monto)
        usuario_ganador.modificar_saldo(-monto)
        
        vendedor.remover_producto(producto)
        usuario_ganador.agregar_producto(producto)
        
        # Incrementar transacciones completadas
        vendedor.incrementar_transaccion()
        usuario_ganador.incrementar_transaccion()
        
        # Registrar actividades
        vendedor.registrar_actividad(f"Venta: Vendiste {producto.titulo} a {usuario_ganador.nombre} por ${monto:,.2f} vía {pago.medio}")
        usuario_ganador.registrar_actividad(f"Compra: Compraste {producto.titulo} a {vendedor.nombre} por ${monto:,.2f} vía {pago.medio}")
        
        # Notificar
        vendedor.agregar_notificacion(f"¡Venta concretada! Vendiste '{producto.titulo}' a {usuario_ganador.nombre} por ${monto:,.2f}.", "exito")
        usuario_ganador.agregar_notificacion(f"¡Compra completada! Compraste '{producto.titulo}' a {vendedor.nombre} por ${monto:,.2f}.", "exito")

        # Guardamos el estado de la compra para habilitar devoluciones
        self.comprador_final = usuario_ganador
        self.vendedor_final = vendedor
        self.monto_pagado = monto
        self.fecha_compra = datetime.datetime.now()
        self.estado_devolucion = "Disponible"
        auto_save()

    def mostrar_historial(self):
        return [f"Venta finalizada por ${o.monto:,.2f}" for o in self.ofertas_list if o.estado == "Aceptada"]

    # ------------------------------------------------------------------
    # DEVOLUCIÓN DE PRODUCTO
    # ------------------------------------------------------------------
    def dias_desde_compra(self):
        if not self.fecha_compra:
            return None
        return (datetime.datetime.now() - self.fecha_compra).days

    def puede_solicitar_devolucion(self):
        if self.estado_devolucion != "Disponible":
            return False
        dias = self.dias_desde_compra()
        return dias is not None and dias <= self.PLAZO_DEVOLUCION_DIAS

    def solicitar_devolucion(self, publicacion, comprador, motivo: str):
        if comprador != self.comprador_final:
            raise ValueError("Solo quien realizó la compra puede solicitar la devolución.")
        if not self.puede_solicitar_devolucion():
            raise ValueError(f"Ya no podés solicitar la devolución (el plazo es de {self.PLAZO_DEVOLUCION_DIAS} días desde la compra).")
        if not motivo or not motivo.strip():
            raise ValueError("Tenés que indicar un motivo para la devolución.")

        self.estado_devolucion = "Solicitada"
        self.motivo_devolucion = motivo.strip()

        comprador.registrar_actividad(f"Devolución: Solicitaste la devolución de '{publicacion.producto.titulo}' (motivo: {motivo.strip()})")
        self.vendedor_final.agregar_notificacion(
            f"{comprador.nombre} solicitó devolver '{publicacion.producto.titulo}'. Motivo: {motivo.strip()}", "info"
        )
        auto_save()

    def resolver_devolucion(self, publicacion, aprobar: bool):
        if self.estado_devolucion != "Solicitada":
            raise ValueError("No hay ninguna devolución pendiente para resolver.")

        producto = publicacion.producto
        comprador = self.comprador_final
        vendedor = self.vendedor_final

        if aprobar:
            # Revertir: el dinero vuelve al comprador, el producto vuelve al vendedor
            vendedor.modificar_saldo(-self.monto_pagado)
            comprador.modificar_saldo(self.monto_pagado)

            comprador.remover_producto(producto)
            vendedor.agregar_producto(producto)

            self.estado_devolucion = "Aprobada"

            vendedor.registrar_actividad(f"Devolución: Aceptaste la devolución de '{producto.titulo}' y reembolsaste ${self.monto_pagado:,.2f}")
            comprador.registrar_actividad(f"Devolución: Te devolvieron ${self.monto_pagado:,.2f} por '{producto.titulo}'")

            comprador.agregar_notificacion(f"Tu devolución de '{producto.titulo}' fue aprobada. Te reembolsamos ${self.monto_pagado:,.2f}.", "exito")
            vendedor.agregar_notificacion(f"Aprobaste la devolución de '{producto.titulo}'. El producto volvió a tu inventario.", "info")
        else:
            self.estado_devolucion = "Rechazada"
            vendedor.registrar_actividad(f"Devolución: Rechazaste la solicitud de devolución de '{producto.titulo}'")
            comprador.agregar_notificacion(f"{vendedor.nombre} rechazó tu solicitud de devolución de '{producto.titulo}'.", "error")
        auto_save()


class Empenio(Modalidad):
    def __init__(self, monto_prestamo: float, plazo_dias: int, tasa_interes: float = 10.0):
        self.monto_prestamo = monto_prestamo
        self.plazo_dias = plazo_dias
        self.tasa_interes = tasa_interes
        self.prestamista = None
        self.estado = "Pendiente"  # "Pendiente", "Activo", "Devuelto", "Vencido"
        self.fecha_inicio = None
        
    def registrar_postulacion(self, publicacion, usuario_interesado, **kwargs):
        if usuario_interesado.saldo < self.monto_prestamo:
            raise ValueError("No tenés suficiente saldo para financiar este empeño.")
        self.prestamista = usuario_interesado
        auto_save()
        
    def ejecutar_intercambio(self, publicacion, usuario_ganador):
        producto = publicacion.producto
        propietario = publicacion.duenio
        prestamista = self.prestamista
        
        if not prestamista:
            raise ValueError("No hay un prestamista postulado.")
            
        # El prestamista le entrega el dinero al propietario
        prestamista.modificar_saldo(-self.monto_prestamo)
        propietario.modificar_saldo(self.monto_prestamo)
        
        # El producto pasa a manos del prestamista (en custodia/empeño)
        propietario.remover_producto(producto)
        prestamista.agregar_producto(producto)
        
        self.estado = "Activo"
        self.fecha_inicio = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Incrementar transacciones
        propietario.incrementar_transaccion()
        prestamista.incrementar_transaccion()
        
        # Registrar actividades
        propietario.registrar_actividad(f"Empeño: Empeñaste {producto.titulo} por ${self.monto_prestamo:,.2f} a {prestamista.nombre}")
        prestamista.registrar_actividad(f"Préstamo: Financiaste el empeño de {producto.titulo} a {propietario.nombre} por ${self.monto_prestamo:,.2f}")
        
        # Notificar
        propietario.agregar_notificacion(f"¡Empeño financiado! Recibiste ${self.monto_prestamo:,.2f} de {prestamista.nombre}.", "exito")
        prestamista.agregar_notificacion(f"¡Préstamo otorgado! Financiaste el empeño de '{producto.titulo}' por ${self.monto_prestamo:,.2f}.", "exito")
        auto_save()


class Publicacion:
    def __init__(self, producto: Producto, modalidad: Modalidad):
        self.producto = producto
        self.duenio = producto.duenio
        self.modalidad = modalidad
        self.postulantes = ObservableList(callback=auto_save)
        self.activa = True
        self.fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
    def postularse(self, usuario_interesado, **kwargs):
        if not self.activa:
            raise ValueError("La publicación ya está cerrada.")
        if usuario_interesado == self.duenio:
            raise ValueError("No podés postularte a tu propio producto.")
        if usuario_interesado not in self.postulantes:
            self.postulantes.append(usuario_interesado)
        self.modalidad.registrar_postulacion(self, usuario_interesado, **kwargs)
        auto_save()
        
    def seleccionar_ganador(self, usuario_ganador):
        if not self.activa:
            raise ValueError("Esta publicación ya fue finalizada.")
        if usuario_ganador not in self.postulantes:
            raise ValueError("El usuario elegido no está en la lista de postulantes.")
        self.modalidad.ejecutar_intercambio(self, usuario_ganador)
        self.activa = False
        auto_save()

    @property
    def tipo(self):
        if isinstance(self.modalidad, Venta):
            return "Venta"
        elif isinstance(self.modalidad, Empenio):
            return "Empeño"
        return "Otro"
        
    @property
    def detalle(self):
        if isinstance(self.modalidad, Venta):
            return f"Medio: {self.modalidad.medio_pago_preferido}"
        elif isinstance(self.modalidad, Empenio):
            return f"Plazo solicitado: {self.modalidad.plazo_dias} días"
        return ""
        
    @property
    def costo_o_plazo(self):
        if isinstance(self.modalidad, Venta):
            return f"$ {self.modalidad.precio_sugerido:,.0f}"
        elif isinstance(self.modalidad, Empenio):
            return f"$ {self.modalidad.monto_prestamo:,.0f}"
        return ""


class PublicacionTrueque:
    def __init__(self, producto_ofrecido: Producto, producto_buscado: str, descripcion_busqueda: str, ofertante: Usuario):
        self.producto_ofrecido = producto_ofrecido
        self.producto_buscado = producto_buscado
        self.descripcion_busqueda = descripcion_busqueda
        self.ofertante = ofertante
        self.fecha = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        
    @property
    def tipo(self):
        return "Trueque"
        
    @property
    def producto(self):
        return self.producto_ofrecido
        
    @property
    def duenio(self):
        return self.ofertante
        
    @property
    def activa(self):
        # Para compatibilidad con filtros
        return True
        
    @property
    def detalle(self):
        return f"Busca a cambio: {self.producto_buscado}"
        
    @property
    def costo_o_plazo(self):
        return "Trueque Abierto"


class PublicacionMercado:
    def __init__(self, producto: Producto, tipo_modalidad: str, detalle_extra: str, costo_o_plazo: str):
        self.producto = producto
        self.tipo = tipo_modalidad 
        self.detalle = detalle_extra
        self.costo_o_plazo = costo_o_plazo


class MensajeChat:
    """
    Representa un mensaje en el chat privado de usuario a usuario.
    """
    def __init__(self, emisor: Usuario, receptor: Usuario, texto: str, leido: bool = False):
        self.emisor = emisor
        self.receptor = receptor
        self.texto = texto
        self.hora = datetime.datetime.now().strftime("%H:%M")
        self.leido = leido



class SistemaPlataforma:
    def __init__(self):
        self._cargando = False
        self.db_path = "plataforma_db.json"
        self.last_mtime = 0.0
        
        global _save_hook
        _save_hook = self.guardar_db
        
        self.usuarios = {}
        self.publicaciones_inicio = ObservableList(callback=self.guardar_db)
        self.publicaciones_trueque = ObservableList(callback=self.guardar_db)
        self.publicaciones_venta = ObservableList(callback=self.guardar_db)
        self.publicaciones_empenio = ObservableList(callback=self.guardar_db)
        self.usuario_logueado = None
        self.mensajes_chat = ObservableList(callback=self.guardar_db)
        
        # Configuración de Firebase
        self.usar_firebase = False
        self.firebase_url = ""
        self.last_update_val = None
        self.config_path = "firebase_config.json"
        self.cargar_config_firebase()
        
        self.cargar_db()

        
    def registrar_transaccion(self, tipo, producto, detalle, monto, estado):
        pass

    @property
    def last_update_token(self):
        return self.last_update_val if self.usar_firebase else self.last_mtime

    def cargar_config_firebase(self):
        if not os.path.exists(self.config_path):
            config = {
                "usar_firebase": False,
                "firebase_url": "https://tu-proyecto.firebaseio.com/"
            }
            try:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                print(f"Error creando config firebase: {e}")
        else:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.usar_firebase = config.get("usar_firebase", False)
                url = config.get("firebase_url", "").strip()
                if url:
                    if not url.endswith("/"):
                        url += "/"
                    self.firebase_url = url
            except Exception as e:
                print(f"Error cargando config firebase: {e}")
                self.usar_firebase = False


    def registrar_usuario(self, nombre: str, password: str, saldo_inicial: float = 0.0) -> Usuario:
        try:
            self.cargar_db()
        except Exception:
            pass
            
        nombre_clean = str(nombre).strip()
        if not nombre_clean:
            raise ValueError("El nombre de usuario no puede estar vacío.")
        if nombre_clean.lower() in [u.lower() for u in self.usuarios.keys()]:
            raise ValueError("El nombre de usuario ya está registrado.")
        
        nuevo_usuario = Usuario(nombre=nombre_clean, password=password, saldo_inicial=saldo_inicial)
        self.usuarios[nombre_clean] = nuevo_usuario
        auto_save()
        return nuevo_usuario

    def obtener_contactos(self, usuario: Usuario):
        return [u for u in self.usuarios.values() if u != usuario]

    def obtener_conversacion(self, usuario: Usuario, contacto: Usuario):
        return [
            msg for msg in self.mensajes_chat
            if (msg.emisor.nombre == usuario.nombre and msg.receptor.nombre == contacto.nombre) or
               (msg.emisor.nombre == contacto.nombre and msg.receptor.nombre == usuario.nombre)
        ]

    def cantidad_mensajes_no_leidos(self, usuario: Usuario):
        return sum(
            1 for msg in self.mensajes_chat
            if msg.receptor.nombre == usuario.nombre and not getattr(msg, "leido", False)
        )

    def marcar_mensajes_leidos(self, usuario: Usuario, contacto: Usuario):
        modificado = False
        for msg in self.mensajes_chat:
            if msg.emisor.nombre == contacto.nombre and msg.receptor.nombre == usuario.nombre and not getattr(msg, "leido", False):
                msg.leido = True
                modificado = True
        if modificado:
            self.guardar_db()


    def enviar_mensaje(self, emisor: Usuario, receptor: Usuario, texto: str):
        if not texto or not texto.strip():
            raise ValueError("El mensaje no puede estar vacío.")
            
        try:
            self.cargar_db()
        except Exception:
            pass
            
        # Rebind references
        emisor_obj = self.usuarios.get(emisor.nombre, emisor)
        receptor_obj = self.usuarios.get(receptor.nombre, receptor)
        
        nuevo_msg = MensajeChat(emisor_obj, receptor_obj, texto.strip())
        self.mensajes_chat.append(nuevo_msg)
        return nuevo_msg
        
    def guardar_db(self):
        if getattr(self, "_cargando", False):
            return
            
        global _save_hook
        temp_hook = _save_hook
        _save_hook = None
        
        try:
            db_data = {
                "usuarios": [],
                "productos": [],
                "publicaciones_trueque": [],
                "publicaciones_venta": [],
                "publicaciones_empenio": [],
                "mensajes_chat": []
            }

            
            # Serialize users
            for u in self.usuarios.values():
                db_data["usuarios"].append({
                    "nombre": u.nombre,
                    "password": u._password,
                    "saldo": u.saldo,
                    "reputacion": u.reputacion,
                    "transacciones_completadas": u.transacciones_completadas,
                    "avatar_path": u.avatar_path,
                    "banco_vinculado": u.banco_vinculado,
                    "banco_nombre": u.banco_nombre,
                    "cbu_alias": u.cbu_alias,
                    "tarjeta_nro": u.tarjeta_nro,
                    "notificaciones": u.notificaciones,
                    "actividades": u.actividades
                })
                
                # Collect products
                for prod in u._productos_propios:
                    db_data["productos"].append({
                        "titulo": prod.titulo,
                        "descripcion": prod.descripcion,
                        "duenio_nombre": u.nombre,
                        "imagen_path": prod.imagen_path
                    })
                    
            # Serialize chat
            for msg in self.mensajes_chat:
                db_data["mensajes_chat"].append({
                    "emisor": msg.emisor.nombre,
                    "receptor": msg.receptor.nombre,
                    "texto": msg.texto,
                    "hora": msg.hora,
                    "leido": getattr(msg, "leido", False)
                })

                
            # Serialize trueques
            for pt in self.publicaciones_trueque:
                db_data["publicaciones_trueque"].append({
                    "producto_ofrecido_titulo": pt.producto_ofrecido.titulo,
                    "producto_ofrecido_duenio": pt.producto_ofrecido.duenio.nombre if pt.producto_ofrecido.duenio else None,
                    "producto_buscado": pt.producto_buscado,
                    "descripcion_busqueda": pt.descripcion_busqueda,
                    "ofertante_nombre": pt.ofertante.nombre,
                    "fecha": pt.fecha
                })
                
            # Serialize Venta publications
            for p in self.publicaciones_venta:
                mod = p.modalidad
                modalidad_data = {
                    "precio_sugerido": mod.precio_sugerido,
                    "medio_pago_preferido": mod.medio_pago_preferido,
                    "ofertas": {u.nombre: monto for u, monto in mod.ofertas.items()},
                    "pagos": {u.nombre: {"monto": pay.monto, "medio": pay.medio, "estado": pay.estado} for u, pay in mod.pagos.items()},
                    "ofertas_list": [{"comprador": of.comprador.nombre, "monto": of.monto, "medio_pago": of.medio_pago, "estado": of.estado} for of in mod.ofertas_list],
                    "comprador_final": mod.comprador_final.nombre if mod.comprador_final else None,
                    "vendedor_final": mod.vendedor_final.nombre if mod.vendedor_final else None,
                    "monto_pagado": mod.monto_pagado,
                    "fecha_compra": mod.fecha_compra.isoformat() if mod.fecha_compra else None,
                    "estado_devolucion": mod.estado_devolucion,
                    "motivo_devolucion": mod.motivo_devolucion
                }
                db_data["publicaciones_venta"].append({
                    "producto_titulo": p.producto.titulo,
                    "producto_duenio": p.producto.duenio.nombre if p.producto.duenio else None,
                    "activa": p.activa,
                    "fecha": p.fecha,
                    "postulantes": [u.nombre for u in p.postulantes],
                    "modalidad": modalidad_data
                })

            # Serialize Empenio publications
            for p in self.publicaciones_empenio:
                mod = p.modalidad
                modalidad_data = {
                    "monto_prestamo": mod.monto_prestamo,
                    "plazo_dias": mod.plazo_dias,
                    "tasa_interes": mod.tasa_interes,
                    "prestamista_nombre": mod.prestamista.nombre if mod.prestamista else None,
                    "estado": mod.estado,
                    "fecha_inicio": mod.fecha_inicio
                }
                db_data["publicaciones_empenio"].append({
                    "producto_titulo": p.producto.titulo,
                    "producto_duenio": p.producto.duenio.nombre if p.producto.duenio else None,
                    "activa": p.activa,
                    "fecha": p.fecha,
                    "postulantes": [u.nombre for u in p.postulantes],
                    "modalidad": modalidad_data
                })

                
            if self.usar_firebase:
                _firebase_http(self.firebase_url + "plataforma_db.json", method="PUT", data=db_data)
                new_update = str(time.time())
                _firebase_http(self.firebase_url + "last_update.json", method="PUT", data=new_update)
                self.last_update_val = new_update
            else:
                temp_path = self.db_path + ".tmp"
                for attempt in range(5):
                    try:
                        with open(temp_path, "w", encoding="utf-8") as f:
                            json.dump(db_data, f, ensure_ascii=False, indent=4)
                        if os.path.exists(self.db_path):
                            os.remove(self.db_path)
                        os.rename(temp_path, self.db_path)
                        break
                    except OSError:
                        time.sleep(0.05)
                        
                try:
                    self.last_mtime = os.path.getmtime(self.db_path)
                except OSError:
                    self.last_mtime = 0.0

                
        finally:
            _save_hook = temp_hook

    def cargar_db(self):
        if self.usar_firebase:
            try:
                current_update = _firebase_http(self.firebase_url + "last_update.json")
            except Exception:
                current_update = None
                
            if current_update == self.last_update_val and self.last_update_val is not None:
                return
                
            data = _firebase_http(self.firebase_url + "plataforma_db.json")
            if data is None:
                self.generar_datos_prueba()
                self.guardar_db()
                return
            current_mtime = 0.0
        else:
            if not os.path.exists(self.db_path):
                self.generar_datos_prueba()
                self.guardar_db()
                return
                
            try:
                current_mtime = os.path.getmtime(self.db_path)
            except OSError:
                current_mtime = 0.0
                
            if current_mtime == self.last_mtime:
                return
                
            data = None
            for attempt in range(5):
                try:
                    with open(self.db_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    break
                except (OSError, json.JSONDecodeError):
                    time.sleep(0.05)
                    
            if data is None:
                return

            
        self._cargando = True
        
        global _save_hook
        temp_hook = _save_hook
        _save_hook = None
        
        try:
            new_usuarios = {}
            for u_data in data.get("usuarios", []):
                u = Usuario(
                    nombre=u_data["nombre"],
                    saldo_inicial=u_data.get("saldo", 0.0),
                    password=u_data.get("password", ""),
                    reputacion=u_data.get("reputacion", 5.0),
                    transacciones=u_data.get("transacciones_completadas", 0),
                    avatar_path=u_data.get("avatar_path", "")
                )
                u.banco_vinculado = u_data.get("banco_vinculado", False)
                u.banco_nombre = u_data.get("banco_nombre", "")
                u.cbu_alias = u_data.get("cbu_alias", "")
                u.tarjeta_nro = u_data.get("tarjeta_nro", "")
                
                u._productos_propios = ObservableList(callback=self.guardar_db)
                u._notificaciones = ObservableList(u_data.get("notificaciones", []), callback=self.guardar_db)
                u._actividades = ObservableList(u_data.get("actividades", []), callback=self.guardar_db)
                
                new_usuarios[u_data["nombre"]] = u
                
            self.usuarios = new_usuarios
            
            all_products = []
            for p_data in data.get("productos", []):
                duenio = self.usuarios.get(p_data.get("duenio_nombre"))
                prod = Producto(
                    titulo=p_data["titulo"],
                    descripcion=p_data.get("descripcion", ""),
                    duenio=None,
                    imagen_path=p_data.get("imagen_path", "")
                )
                if duenio:
                    duenio.agregar_producto(prod)
                all_products.append(prod)
                
            new_mensajes_chat = []
            for msg_data in data.get("mensajes_chat", []):
                emisor = self.usuarios.get(msg_data.get("emisor"))
                receptor = self.usuarios.get(msg_data.get("receptor"))
                if emisor and receptor:
                    msg = MensajeChat(emisor, receptor, msg_data.get("texto", ""), leido=msg_data.get("leido", False))
                    msg.hora = msg_data.get("hora", datetime.datetime.now().strftime("%H:%M"))
                    new_mensajes_chat.append(msg)
            self.mensajes_chat = ObservableList(new_mensajes_chat, callback=self.guardar_db)

            
            new_publicaciones_trueque = []
            for pt_data in data.get("publicaciones_trueque", []):
                prod = next((p for p in all_products if p.titulo == pt_data.get("producto_ofrecido_titulo") and p.duenio and p.duenio.nombre == pt_data.get("producto_ofrecido_duenio")), None)
                ofertante = self.usuarios.get(pt_data.get("ofertante_nombre"))
                if prod and ofertante:
                    pt = PublicacionTrueque(prod, pt_data.get("producto_buscado", ""), pt_data.get("descripcion_busqueda", ""), ofertante)
                    pt.fecha = pt_data.get("fecha", "")
                    new_publicaciones_trueque.append(pt)
            self.publicaciones_trueque = ObservableList(new_publicaciones_trueque, callback=self.guardar_db)
            new_publicaciones_venta = []
            new_publicaciones_empenio = []
            
            # 1. Cargar desde publicaciones_venta (si existe)
            if "publicaciones_venta" in data:
                for p_data in data.get("publicaciones_venta", []):
                    prod = next((p for p in all_products if p.titulo == p_data.get("producto_titulo") and p.duenio and p.duenio.nombre == p_data.get("producto_duenio")), None)
                    if not prod:
                        prod = next((p for p in all_products if p.titulo == p_data.get("producto_titulo")), None)
                    if not prod:
                        continue
                    
                    mod_data = p_data.get("modalidad", {})
                    mod = Venta(mod_data.get("precio_sugerido", 0.0), mod_data.get("medio_pago_preferido", ""))
                    mod.ofertas = {self.usuarios[u_name]: monto for u_name, monto in mod_data.get("ofertas", {}).items() if u_name in self.usuarios}
                    
                    for u_name, pay_info in mod_data.get("pagos", {}).items():
                        if u_name in self.usuarios:
                            pago = Pago(pay_info.get("monto", 0.0), pay_info.get("medio", ""))
                            pago.estado = pay_info.get("estado", "Pendiente")
                            mod.pagos[self.usuarios[u_name]] = pago
                            
                    mod.ofertas_list = []
                    for of_info in mod_data.get("ofertas_list", []):
                        u_name = of_info.get("comprador")
                        if u_name in self.usuarios:
                            of = Oferta(self.usuarios[u_name], of_info.get("monto", 0.0), of_info.get("medio_pago", ""))
                            of.estado = of_info.get("estado", "Pendiente")
                            mod.ofertas_list.append(of)
                            
                    if mod_data.get("comprador_final") and mod_data["comprador_final"] in self.usuarios:
                        mod.comprador_final = self.usuarios[mod_data["comprador_final"]]
                    if mod_data.get("vendedor_final") and mod_data["vendedor_final"] in self.usuarios:
                        mod.vendedor_final = self.usuarios[mod_data["vendedor_final"]]
                    mod.monto_pagado = mod_data.get("monto_pagado", 0.0)
                    if mod_data.get("fecha_compra"):
                        mod.fecha_compra = datetime.datetime.fromisoformat(mod_data["fecha_compra"])
                    mod.estado_devolucion = mod_data.get("estado_devolucion", "Ninguna")
                    mod.motivo_devolucion = mod_data.get("motivo_devolucion", "")
                    
                    pub = Publicacion(prod, mod)
                    pub.activa = p_data.get("activa", True)
                    pub.fecha = p_data.get("fecha", "")
                    pub.postulantes = [self.usuarios[u_name] for u_name in p_data.get("postulantes", []) if u_name in self.usuarios]
                    new_publicaciones_venta.append(pub)
            
            # 2. Cargar desde publicaciones_empenio (si existe)
            if "publicaciones_empenio" in data:
                for p_data in data.get("publicaciones_empenio", []):
                    prod = next((p for p in all_products if p.titulo == p_data.get("producto_titulo") and p.duenio and p.duenio.nombre == p_data.get("producto_duenio")), None)
                    if not prod:
                        prod = next((p for p in all_products if p.titulo == p_data.get("producto_titulo")), None)
                    if not prod:
                        continue
                    
                    mod_data = p_data.get("modalidad", {})
                    mod = Empenio(mod_data.get("monto_prestamo", 0.0), mod_data.get("plazo_dias", 30), mod_data.get("tasa_interes", 10.0))
                    if mod_data.get("prestamista_nombre") and mod_data["prestamista_nombre"] in self.usuarios:
                        mod.prestamista = self.usuarios[mod_data["prestamista_nombre"]]
                    mod.estado = mod_data.get("estado", "Pendiente")
                    mod.fecha_inicio = mod_data.get("fecha_inicio")
                    
                    pub = Publicacion(prod, mod)
                    pub.activa = p_data.get("activa", True)
                    pub.fecha = p_data.get("fecha", "")
                    pub.postulantes = [self.usuarios[u_name] for u_name in p_data.get("postulantes", []) if u_name in self.usuarios]
                    new_publicaciones_empenio.append(pub)
            
            # 3. Fallback retrocompatible si no existen los nodos nuevos pero sí el nodo unificado 'publicaciones'
            if "publicaciones_venta" not in data and "publicaciones_empenio" not in data and "publicaciones" in data:
                for p_data in data.get("publicaciones", []):
                    prod = next((p for p in all_products if p.titulo == p_data.get("producto_titulo") and p.duenio and p.duenio.nombre == p_data.get("producto_duenio")), None)
                    if not prod:
                        prod = next((p for p in all_products if p.titulo == p_data.get("producto_titulo")), None)
                    if not prod:
                        continue
                        
                    mod_data = p_data.get("modalidad", {})
                    if mod_data.get("tipo") == "Venta":
                        mod = Venta(mod_data.get("precio_sugerido", 0.0), mod_data.get("medio_pago_preferido", ""))
                        mod.ofertas = {self.usuarios[u_name]: monto for u_name, monto in mod_data.get("ofertas", {}).items() if u_name in self.usuarios}
                        
                        for u_name, pay_info in mod_data.get("pagos", {}).items():
                            if u_name in self.usuarios:
                                pago = Pago(pay_info.get("monto", 0.0), pay_info.get("medio", ""))
                                pago.estado = pay_info.get("estado", "Pendiente")
                                mod.pagos[self.usuarios[u_name]] = pago
                                
                        mod.ofertas_list = []
                        for of_info in mod_data.get("ofertas_list", []):
                            u_name = of_info.get("comprador")
                            if u_name in self.usuarios:
                                of = Oferta(self.usuarios[u_name], of_info.get("monto", 0.0), of_info.get("medio_pago", ""))
                                of.estado = of_info.get("estado", "Pendiente")
                                mod.ofertas_list.append(of)
                                
                        if mod_data.get("comprador_final") and mod_data["comprador_final"] in self.usuarios:
                            mod.comprador_final = self.usuarios[mod_data["comprador_final"]]
                        if mod_data.get("vendedor_final") and mod_data["vendedor_final"] in self.usuarios:
                            mod.vendedor_final = self.usuarios[mod_data["vendedor_final"]]
                        mod.monto_pagado = mod_data.get("monto_pagado", 0.0)
                        if mod_data.get("fecha_compra"):
                            mod.fecha_compra = datetime.datetime.fromisoformat(mod_data["fecha_compra"])
                        mod.estado_devolucion = mod_data.get("estado_devolucion", "Ninguna")
                        mod.motivo_devolucion = mod_data.get("motivo_devolucion", "")
                        
                        pub = Publicacion(prod, mod)
                        pub.activa = p_data.get("activa", True)
                        pub.fecha = p_data.get("fecha", "")
                        pub.postulantes = [self.usuarios[u_name] for u_name in p_data.get("postulantes", []) if u_name in self.usuarios]
                        new_publicaciones_venta.append(pub)
                        
                    elif mod_data.get("tipo") == "Empeño":
                        mod = Empenio(mod_data.get("monto_prestamo", 0.0), mod_data.get("plazo_dias", 30), mod_data.get("tasa_interes", 10.0))
                        if mod_data.get("prestamista_nombre") and mod_data["prestamista_nombre"] in self.usuarios:
                            mod.prestamista = self.usuarios[mod_data["prestamista_nombre"]]
                        mod.estado = mod_data.get("estado", "Pendiente")
                        mod.fecha_inicio = mod_data.get("fecha_inicio")
                        
                        pub = Publicacion(prod, mod)
                        pub.activa = p_data.get("activa", True)
                        pub.fecha = p_data.get("fecha", "")
                        pub.postulantes = [self.usuarios[u_name] for u_name in p_data.get("postulantes", []) if u_name in self.usuarios]
                        new_publicaciones_empenio.append(pub)

                    
            self.publicaciones_venta = ObservableList(new_publicaciones_venta, callback=self.guardar_db)
            self.publicaciones_empenio = ObservableList(new_publicaciones_empenio, callback=self.guardar_db)
            
            new_publicaciones_inicio = []
            for pt in self.publicaciones_trueque:
                new_publicaciones_inicio.append(pt)
            for pv in self.publicaciones_venta:
                new_publicaciones_inicio.append(pv)
            for pe in self.publicaciones_empenio:
                new_publicaciones_inicio.append(pe)
                
            self.publicaciones_inicio = ObservableList(new_publicaciones_inicio, callback=self.guardar_db)
            if self.usuario_logueado:
                self.usuario_logueado = self.usuarios.get(self.usuario_logueado.nombre, self.usuario_logueado)
            
            if self.usar_firebase:
                self.last_update_val = current_update
            else:
                self.last_mtime = current_mtime



            
        finally:
            self._cargando = False
            _save_hook = temp_hook

    def generar_datos_prueba(self):
        marcos = Usuario("Marcos", 42000.0)
        lucas = Usuario("Lucas", 30000.0)
        
        self.usuarios = {
            "Marcos": marcos,
            "Lucas": lucas
        }
        
        p2 = Producto("Reloj Seiko", "Reloj cronógrafo vintage automático.", marcos, os.path.join("assets", "images", "RelojSeiko.jpg"))
        p3 = Producto("Cámara Nikon", "Réflex digital en caja original.", marcos, os.path.join("assets", "images", "CamaraNikon.jpg"))
        p4 = Producto("Cadena de plata", "Joyas finas de plata 925.", lucas, os.path.join("assets", "images", "CadenaDePlata.jpg"))
        p5 = Producto("Guitarra Acústica", "Fender acústica en buen estado.", lucas, os.path.join("assets", "images", "GuitarraFender.jpg"))
        p7 = Producto("Casco de Samurai", "Kabuto del período Edo en excelente estado.", marcos, os.path.join("assets", "images", "KabutoEdo.jpg"))
        p9 = Producto("Estilográfica de Oro", "Pluma Montblanc con plumín de oro 14k.", lucas, os.path.join("assets", "images", "PlumaMontblanc.jpg"))
        p10 = Producto("Libro Primera Edición", "El Quijote ilustrado por Dalí, edición numerada.", marcos, os.path.join("assets", "images", "LibroQuijoteIlustrado.webp"))
        
        self.publicaciones_trueque.clear()
        self.publicaciones_trueque.extend([
            PublicacionTrueque(p5, "Notebook", "Cambio mano a mano por mi notebook.", lucas),
            PublicacionTrueque(p9, "Reloj antiguo", "Cambio pluma fina por reloj antiguo.", lucas)
        ])
        
        self.publicaciones_inicio.clear()
        for pt in self.publicaciones_trueque:
            self.publicaciones_inicio.append(pt)

        self.publicaciones_venta.clear()
        
        modalidad_venta_p2 = Venta(precio_sugerido=22000.0, medio_pago_preferido="Transferencia")
        pub_venta_p2 = Publicacion(p2, modalidad_venta_p2)
        self.publicaciones_venta.append(pub_venta_p2)
        self.publicaciones_inicio.append(pub_venta_p2)

        modalidad_venta_p10 = Venta(precio_sugerido=18000.0, medio_pago_preferido="Mercado Pago")
        pub_venta_p10 = Publicacion(p10, modalidad_venta_p10)
        self.publicaciones_venta.append(pub_venta_p10)
        self.publicaciones_inicio.append(pub_venta_p10)

        self.publicaciones_empenio.clear()
        
        modalidad_empenio_p7 = Empenio(monto_prestamo=45000.0, plazo_dias=90, tasa_interes=15.0)
        pub_empenio_p7 = Publicacion(p7, modalidad_empenio_p7)
        self.publicaciones_empenio.append(pub_empenio_p7)
        self.publicaciones_inicio.append(pub_empenio_p7)

        new_mensajes_chat = [
            MensajeChat(marcos, lucas, "Hola Lucas, ¿seguís teniendo la guitarra acústica?"),
            MensajeChat(lucas, marcos, "Hola Marcos! Sí, la tengo. ¿Te interesa?")
        ]
        self.mensajes_chat.clear()
        self.mensajes_chat.extend(new_mensajes_chat)

        modalidad_venta_completada = Venta(30000.0, "Transferencia")
        modalidad_venta_completada.comprador_final = lucas
        modalidad_venta_completada.vendedor_final = marcos
        modalidad_venta_completada.monto_pagado = 30000.0
        modalidad_venta_completada.fecha_compra = datetime.datetime.now()
        modalidad_venta_completada.estado_devolucion = "Disponible"
        
        marcos.remover_producto(p3)
        lucas.agregar_producto(p3)
        
        pub_venta_completada = Publicacion(p3, modalidad_venta_completada)
        pub_venta_completada.activa = False
        
        self.publicaciones_venta.append(pub_venta_completada)