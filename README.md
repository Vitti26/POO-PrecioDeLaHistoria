# 🏛️ El Precio de la Historia — Plataforma de Coleccionismo

¡Bienvenido a **El Precio de la Historia**! Esta es una aplicación de escritorio premium diseñada para coleccionistas. Permite a los usuarios registrarse, gestionar sus colecciones de objetos raros e históricos, y realizar transacciones a través de tres modalidades principales: **Trueques**, **Ventas** y **Empeños**, además de contar con un sistema de **Chat Privado** en tiempo real para negociar las ofertas.

---

## 📋 Descripción del Sistema

La plataforma simula un mercado dinámico de intercambio de reliquias y coleccionables. Sus principales módulos y funcionalidades son:

1. **Acceso y Registro Seguro**: 
   * Pantalla de inicio de sesión con validación de credenciales.
   * Registro de nuevos usuarios asignándoles un saldo inicial ficticio para operar.
2. **Mercado Principal (Inicio)**: 
   * Una vista moderna tipo "catálogo" con tarjetas de los productos activos.
   * Buscador dinámico que filtra artículos en tiempo real por título o palabras clave.
   * Información del vendedor, tipo de transacción e imágenes del producto.
3. **Módulo de Trueques**:
   * Intercambio directo de objetos "mano a mano".
   * Los ofertantes proponen qué buscan a cambio de su artículo.
4. **Módulo de Ventas**:
   * Publicaciones con precio sugerido y medio de pago preferido.
   * Los interesados pueden enviar ofertas con montos y métodos de pago personalizados.
   * Sistema de devoluciones: Permite al comprador solicitar un reembolso hasta 3 días después de la compra. El vendedor puede decidir si aprueba la devolución (reinvirtiendo el saldo y el producto) o la rechaza.
5. **Módulo de Empeños**:
   * Préstamos monetarios garantizados por un producto que queda en custodia.
   * Los prestamistas financian el empeño entregando el dinero al dueño, cobrando una tasa de interés sobre el plazo estipulado.
6. **Chat de Negociación**:
   * Un chat integrado flotante que permite enviar y recibir mensajes directamente con cualquier otro coleccionista registrado para acordar los intercambios.
7. **Mi Cuenta**:
   * Visualización de datos de perfil, reputación (representada premium con estrellas ★★★★☆) y saldo disponible.
   * Simulación bancaria: Permite vincular cuentas de banco reales/ficticias (banco, CBU, alias, tarjeta) para depositar fondos.
   * Panel de notificaciones dinámico y registro detallado del historial de actividad del usuario.
8. **Facturas y Comprobantes**:
   * Generación automática de comprobantes digitales al concretar compraventas o financiar empeños.
   * La interfaz muestra una factura detallada con datos del artículo, partes involucradas (comprador/vendedor, prestatario/prestamista) y desglose financiero (comisiones, intereses y plazos de devolución), permitiendo exportar el recibo en formato `.txt`.

---

## 🛠️ Decisiones de Diseño (Explicación Sencilla)

El proyecto fue desarrollado utilizando el paradigma de **Programación Orientada a Objetos (POO)** en Python, complementado con una interfaz gráfica moderna. A continuación, se detallan las decisiones arquitectónicas en un lenguaje simple:

### 1. Modelado del Mundo Real (Clases y Objetos)
Dividimos el código siguiendo la lógica del negocio real. Cada concepto importante es una "clase" (un molde) que da vida a objetos independientes:
* **`Usuario`**: Almacena el perfil del coleccionista, su dinero, su reputación y sus pertenencias.
* **`Producto`**: Representa el objeto de colección (título, descripción, imagen y dueño).
* **`Publicacion`**: El contenedor que asocia un producto con una modalidad de intercambio.
* **`MensajeChat`**: Estructura cada mensaje enviado entre usuarios.

### 2. Encapsulación (Seguridad e Integridad de los Datos)
En POO, la *encapsulación* significa ocultar detalles internos de un objeto y protegerlos de modificaciones externas accidentales. 
* **Ejemplo**: El saldo (`saldo`) y los productos (`productos_propios`) de un usuario no se pueden modificar directamente desde la interfaz gráfica o desde otros archivos escribiendo `usuario.saldo = 500`. En su lugar, el objeto expone métodos seguros como `modificar_saldo()` o `agregar_producto()`. Esto evita errores graves como saldos negativos o productos duplicados en el inventario.

### 3. Polimorfismo (Modalidades Flexibles)
El *polimorfismo* nos permite tratar de la misma forma a cosas que se comportan diferente en el fondo.
* **Cómo se aplica**: Las clases `Venta` y `Empenio` heredan de una estructura base llamada `Modalidad`. Tanto el empeño como la venta reaccionan al comando `ejecutar_intercambio()`, pero cada uno realiza acciones distintas por debajo (la venta transfiere la propiedad permanentemente, mientras que el empeño marca el objeto en custodia y define fechas límites). Esto hace que añadir nuevas formas de intercambio a futuro sea extremadamente fácil y ordenado.

### 4. Guardado Automático Inteligente (`ObservableList`)
Diseñamos una lista especial llamada `ObservableList`. Cada vez que agregamos un mensaje de chat, creamos una publicación, registramos una actividad o compramos un producto, esta lista "se da cuenta" del cambio y dispara de forma automática el guardado en el archivo `plataforma_db.json`. 
* **Ventaja**: No se requiere un botón molesto de "Guardar" ni código repetitivo en la UI; todo se guarda de forma transparente en segundo plano.

### 5. Interfaz Premium y Adaptable (CustomTkinter y Utils)
La interfaz visual utiliza `CustomTkinter`, una biblioteca moderna basada en Tkinter que proporciona un tema oscuro nativo muy pulido (estilo *dark gold*).
* Implementamos un sistema de caché de imágenes en [utils.py](file:///c:/Users/Usuario/Desktop/Uni/POO/VersionFinal/utils.py) para que, si falta alguna imagen o falla el disco, la aplicación nunca se rompa y cargue un marcador de posición (*placeholder*) premium por defecto.
* Creamos efectos visuales interactivos (*hover*) que iluminan las tarjetas de productos suavemente al pasar el cursor sobre ellas.
* Diseñamos un cuadro de diálogo especializado (`VistaComprobante`) que simula un ticket o factura electrónica, reforzando la inmersión del coleccionista al cerrar tratos y permitiéndole guardar un registro físico de sus transacciones.

---

## 🚀 Requisitos y Cómo Ejecutar la App

### Requisitos Previos
Asegurate de tener instalado Python 3.8 o superior en tu sistema.

### Instalación de Librerías
Antes de correr el proyecto, instalá las librerías necesarias ejecutando en la terminal de tu sistema:
```bash
pip install customtkinter pillow
```

### Ejecutar el Proyecto
Para iniciar la aplicación, ejecutá el archivo principal desde la carpeta del proyecto:
```bash
python main.py
```

Al abrirse la pantalla de inicio de sesión, podés ingresar con cualquiera de los dos usuarios de prueba preestablecidos (la clave para ambos es `1234`):
* **Marcos**
* **Lucas**

*(También podés hacer clic en **Registrate** para crear un usuario nuevo y empezar de cero).*

---

## 💡 Conclusión

El diseño del software separa limpiamente la lógica de la plataforma (el "cerebro" en `backend.py`) de la interfaz de usuario (las "vistas" en `interfaces/`). Esta modularidad no solo facilita la lectura del código, sino que garantiza que la aplicación sea robusta, extensible y fácil de mantener en el ámbito académico y profesional.
