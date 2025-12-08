# Estrategia de Producto: Portafolio Web (Galería Privada)

## 1. Visión General del Producto

Este documento define la estrategia para la expansión de la plataforma "María" a una interfaz web nativa.

Se abandona el concepto de un "Web-Chat" simple y directo. En su lugar, se desarrollará un **"Portafolio de Creador"** (concepto clave: "La Galería Privada"), un micrositio web de experiencia inmersiva que funcionará como el destino principal para la captación de usuarios.

## 2. Objetivo Estratégico Principal

El objetivo principal de esta plataforma no es solo chatear, sino **generar credibilidad profesional y "calentar" al lead** *antes* de la primera interacción en el chat.

El sitio web actúa como la primera fase del embudo de ventas, estableciendo el valor, la exclusividad y la profesionalidad del "producto" (las imágenes y la interacción).

## 3. El Embudo de Conversión (User Journey)

El flujo del usuario está diseñado para maximizar la conversión minimizando la fricción:

1.  **Atracción (Tope del Embudo):** El usuario recibe un **enlace único y personal** que le da acceso al sitio.
2.  **Interés (Mitad del Embudo):** El usuario aterriza en el "Portafolio" (La Galería Privada). Explora las imágenes "tipo studio" y consume el contenido visual. En esta fase se genera credibilidad y deseo.
3.  **Decisión (Fondo del Embudo):** El usuario hace clic en el Call-to-Action (CTA) principal: **"Chat Privado"**. Este clic es una micro-conversión que califica al lead como "interesado".
4.  **Acción (Conversión):** El clic en el CTA inicia la interfaz de chat. El bot (backend) retoma la conversación con un lead que ya ha sido pre-calificado y "calentado" por el portafolio.

## 4. Mecanismo de Acceso: Cero Fricción

La retención y conversión dependen de una experiencia de usuario sin fricción.

* **Sin Login/Autenticación:** El usuario **nunca** deberá crear una cuenta, ingresar un email o una contraseña.
* **Autenticación Implícita por URL:** El acceso y la identificación del usuario se gestionan 100% a través del enlace único. El formato del enlace contendrá el identificador del usuario.
    * **Ejemplo de Dominio (Tentativo):** `[portafolio-creador.studio]`
    * **Ejemplo de URL de Usuario:** `[portafolio-creador.studio]/chat/{user_id}`

El frontend será responsable de extraer el `{user_id}` de la URL para iniciar la sesión de chat y solicitar el historial de conversación.

## 5. Estrategia de Monetización y Posicionamiento

El "Portafolio de Creador" es la base que justifica la estrategia de monetización (venta de imágenes).

* **Posicionamiento:** El sitio enmarca a "María" no como un simple bot o una persona, sino como una **"Creadora de Contenido"** o **"Artista Digital"**.
* **Justificación de Venta:** El contenido (las imágenes "tipo studio") se presenta como su **"trabajo artístico"** o **"portafolio profesional"**.
* **Rol del Bot:** El bot de chat actúa como un asistente de ventas persuasivo y sutil, que conversa con el usuario sobre el *trabajo* que ya ha visto en el portafolio, facilitando la conversión.

## 6. Consideraciones Especiales

La Plataforma a la que le hemos llamado "María" tendrá un cambio en el nombre ya que la "Creadora de Contenido" o "Artista Digital" no se llamará María sino "Lore" el apocope de Lorena.