# 🔐 Fase 2 — Cifrado Híbrido de Mensajes

## 📌 Descripción general

En esta fase se implementó el módulo de mensajería cifrada del sistema. El objetivo principal fue permitir el envío, almacenamiento, recuperación y descifrado de mensajes protegidos mediante un esquema de cifrado híbrido.

El sistema combina:

- **AES-256-GCM** para cifrar el contenido del mensaje.
- **RSA-OAEP** para cifrar la clave AES efímera utilizada en cada mensaje.
- **Base64** para almacenar de forma segura los componentes binarios del mensaje cifrado.
- **API REST con FastAPI** para exponer las operaciones de envío, recuperación y descifrado.
- **PostgreSQL** para persistir mensajes cifrados y claves AES cifradas por destinatario.

La fase se construyó sobre la base de la Fase 1, donde ya existían usuarios registrados, hashing de contraseñas, generación de llaves RSA y almacenamiento seguro de llaves privadas cifradas.


## 🎯 Objetivo de la fase

El objetivo de esta fase fue implementar un flujo funcional de mensajería segura donde:

1. Un usuario pueda enviar un mensaje a otro usuario.
2. El mensaje nunca se guarde en texto plano.
3. El contenido del mensaje se cifre con AES-256-GCM.
4. La clave AES se proteja cifrándola con la llave pública RSA del destinatario.
5. El destinatario pueda recuperar la clave AES usando su llave privada.
6. El destinatario pueda descifrar el mensaje original.
7. El sistema pueda extenderse para mensajes grupales mediante el uso de una tabla de claves cifradas por usuario.


## 🧠 Modelo criptográfico utilizado

El sistema utiliza un esquema de **cifrado híbrido**.

Este enfoque se usa porque RSA no es ideal para cifrar mensajes largos directamente. Por eso, el mensaje se cifra con AES, que es eficiente para datos arbitrarios, y RSA se usa únicamente para proteger la clave AES.

### Flujo conceptual

1. Se genera una clave AES-256 aleatoria para cada mensaje.
2. Se genera un nonce único para AES-GCM.
3. El plaintext se cifra con AES-256-GCM.
4. La clave AES se cifra con RSA-OAEP usando la llave pública del destinatario.
5. Se almacenan el ciphertext, encrypted_key, nonce, auth_tag y timestamp.
6. Para descifrar, el destinatario recupera su llave privada, descifra la clave AES y luego descifra el mensaje.


## 🔒 Cifrado AES-256-GCM

Se implementó cifrado simétrico con **AES-256-GCM** para proteger el contenido de los mensajes.

AES-GCM aporta dos propiedades importantes:

- **Confidencialidad:** el contenido del mensaje no puede leerse sin la clave AES.
- **Integridad y autenticación:** el tag de GCM permite detectar modificaciones en el ciphertext, nonce o tag.

### Características implementadas

- Se genera una clave AES de 32 bytes.
- Se utiliza un nonce único por mensaje.
- El contenido cifrado se almacena como Base64.
- El nonce se almacena como Base64.
- El tag de autenticación se almacena como Base64.
- Si el tag es alterado, el descifrado falla.

### Funciones relacionadas

- `encrypt_aes_gcm(plaintext, aes_key)`
- `decrypt_aes_gcm(ciphertext_b64, nonce_b64, tag_b64, aes_key)`


## 🔑 Cifrado de clave AES con RSA-OAEP

Para proteger la clave AES utilizada en cada mensaje, se implementó cifrado asimétrico con **RSA-OAEP**.

La clave AES no se almacena directamente. En su lugar, se cifra con la llave pública RSA del destinatario.

### Características implementadas

- Se usa la llave pública del destinatario en formato PEM.
- Se cifra la clave AES con RSA-OAEP.
- Se utiliza OAEP con MGF1 y SHA-256.
- La clave AES cifrada se almacena como Base64.
- Solo el destinatario, usando su llave privada, puede recuperar la clave AES original.

### Funciones relacionadas

- `encrypt_aes_key_with_public_key(aes_key, public_key_pem)`
- `decrypt_aes_key_with_private_key(encrypted_key_b64, private_key_pem)`


## 🔐 Cifrado híbrido para mensajes individuales

Se implementó un flujo completo para cifrar mensajes individuales entre dos usuarios.

### Proceso de envío

1. El remitente envía un mensaje en texto claro al endpoint correspondiente.
2. El sistema busca al destinatario en la base de datos.
3. Se obtiene la llave pública del destinatario.
4. Se genera una clave AES-256 efímera.
5. El mensaje se cifra con AES-256-GCM.
6. La clave AES se cifra con RSA-OAEP.
7. El mensaje cifrado se guarda en la tabla `messages`.
8. La clave AES cifrada se guarda en la tabla `message_keys`.
9. La API devuelve la metadata del mensaje cifrado.

### Función principal utilizada

- `encrypt_message_for_recipient(plaintext, recipient_public_key_pem)`

### Resultado esperado del cifrado

El resultado contiene:

- `ciphertext`
- `encrypted_key`
- `nonce`
- `auth_tag`

Todos los valores binarios se manejan en Base64 para facilitar su almacenamiento y transporte por JSON.


## 👥 Soporte para mensajería grupal

La fase también contempla soporte para mensajes grupales mediante el diseño de almacenamiento con `message_keys`.

La idea central es:

- El mensaje se cifra una sola vez con una clave AES.
- Esa misma clave AES se cifra una vez por cada destinatario.
- Cada usuario del grupo recibe su propia copia cifrada de la clave AES.
- Todas las claves cifradas se almacenan en `message_keys`.

### Ventaja del diseño

Este diseño evita duplicar el mensaje cifrado para cada miembro del grupo. Solo se duplica la clave AES cifrada, no el ciphertext.

### Función relacionada

- `encrypt_message_for_group(plaintext, recipients_public_keys)`

### Estructura esperada

El flujo grupal genera:

- un `ciphertext`
- un `nonce`
- un `auth_tag`
- varias entradas en `encrypted_keys`, una por usuario


## 🗄️ Modelo de almacenamiento

Para soportar mensajes individuales y grupales, se definieron dos tablas principales:

- `messages`
- `message_keys`

Esta separación permite guardar el contenido cifrado una sola vez y asociar una o varias claves AES cifradas dependiendo de si el mensaje es individual o grupal.


## 📨 Tabla `messages`

La tabla `messages` almacena el contenido cifrado del mensaje.

### Campos principales

- `id`
- `sender_id`
- `recipient_id`
- `group_id`
- `ciphertext`
- `nonce`
- `auth_tag`
- `created_at`

### Propósito

Esta tabla representa el mensaje cifrado como entidad principal. No guarda plaintext bajo ninguna circunstancia.

### Consideraciones

- Para mensajes individuales, `recipient_id` contiene el destinatario.
- Para mensajes grupales, `group_id` permite identificar el grupo.
- El campo `ciphertext` contiene únicamente el mensaje cifrado.
- El campo `auth_tag` permite validar la integridad del mensaje durante el descifrado.


## 🔑 Tabla `message_keys`

La tabla `message_keys` almacena la clave AES cifrada para cada destinatario.

### Campos principales

- `id`
- `message_id`
- `user_id`
- `encrypted_key`
- `created_at`

### Propósito

Esta tabla permite que cada destinatario tenga su propia versión cifrada de la clave AES.

### Ventajas

- Permite mensajes individuales y grupales con el mismo diseño.
- Evita exponer claves cifradas de otros usuarios.
- Facilita recuperar únicamente la clave cifrada correspondiente al usuario que consulta.


## 🧩 Modelos y persistencia

Se agregaron modelos y funciones de persistencia para manejar mensajes cifrados y claves cifradas.

### Modelos principales

- `Message`
- `MessageKey`

### Funciones CRUD principales

- `create_message`
- `create_message_key`
- `get_message_by_id`
- `get_message_key_for_user`
- `get_messages_for_user`

Estas funciones permiten crear mensajes, asociar claves cifradas a destinatarios y recuperar mensajes de forma segura.


## 🌐 API REST implementada

Se implementó un router de mensajes en:

- `src/routes/messages.py`

Este router fue registrado en la aplicación principal mediante:

- `src/main.py`

Los endpoints implementados permiten enviar mensajes cifrados, consultar mensajes de un usuario y descifrar mensajes específicos.


## 📤 Endpoint: enviar mensaje cifrado

### Endpoint

POST `/messages`

### Propósito

Permite enviar un mensaje cifrado de un usuario remitente a un usuario destinatario.

### Request esperado

```json
{
  "sender_id": "uuid-remitente",
  "recipient_id": "uuid-destinatario",
  "plaintext": "Mensaje secreto"
}
```

### Flujo interno

1. Se valida que exista el remitente.
2. Se valida que exista el destinatario.
3. Se obtiene la llave pública del destinatario.
4. Se cifra el mensaje con `encrypt_message_for_recipient`.
5. Se guarda el mensaje cifrado en `messages`.
6. Se guarda la clave AES cifrada en `message_keys`.
7. Se devuelve la metadata del mensaje.

### Response esperado

```json
{
  "id": "uuid-mensaje",
  "sender_id": "uuid-remitente",
  "recipient_id": "uuid-destinatario",
  "group_id": null,
  "ciphertext": "...",
  "nonce": "...",
  "auth_tag": "...",
  "created_at": "..."
}
```

### Observación importante

El endpoint no devuelve el plaintext. Esto confirma que el mensaje se almacena y se expone únicamente en su forma cifrada.


## 📥 Endpoint: obtener mensajes de un usuario

### Endpoint

GET `/messages/{user_id}`

### Propósito

Permite obtener los mensajes cifrados dirigidos a un usuario específico.

### Flujo interno

1. Se valida que el usuario exista.
2. Se consultan los mensajes asociados al usuario mediante `message_keys`.
3. Se devuelve cada mensaje con la clave AES cifrada correspondiente a ese usuario.
4. No se devuelven claves cifradas pertenecientes a otros usuarios.

### Response esperado

```json
[
  {
    "id": "uuid-mensaje",
    "sender_id": "uuid-remitente",
    "recipient_id": "uuid-destinatario",
    "group_id": null,
    "ciphertext": "...",
    "encrypted_key": "...",
    "nonce": "...",
    "auth_tag": "...",
    "created_at": "..."
  }
]
```

### Observación importante

El campo `encrypted_key` devuelto corresponde únicamente al usuario que consulta. Esto permite que cada destinatario reciba solo la clave que puede descifrar con su llave privada.


## 🔓 Endpoint: descifrar mensaje

### Endpoint

POST `/messages/{message_id}/decrypt`

### Propósito

Permite demostrar el flujo end-to-end de descifrado de un mensaje.

### Request esperado

```json
{
  "user_id": "uuid-destinatario",
  "password": "password-del-destinatario"
}
```

### Flujo interno

1. Se busca el mensaje por `message_id`.
2. Se busca el usuario por `user_id`.
3. Se busca la entrada de `message_keys` correspondiente a ese mensaje y usuario.
4. Se valida que el usuario tenga permiso para descifrar ese mensaje.
5. Se descifra la llave privada del usuario usando su contraseña.
6. Se descifra la clave AES usando la llave privada.
7. Se descifra el ciphertext usando AES-256-GCM.
8. Se devuelve el plaintext original.

### Response esperado

```json
{
  "message_id": "uuid-mensaje",
  "plaintext": "Mensaje secreto"
}
```

### Observación importante

Este endpoint demuestra que el sistema no solo cifra y almacena mensajes, sino que también permite recuperar el mensaje original únicamente cuando el usuario correcto proporciona su contraseña.


## 🔄 Flujo end-to-end validado

Durante las pruebas manuales en Swagger se validó el siguiente flujo:

1. Se verificó conexión exitosa con PostgreSQL usando `GET /db-test`.
2. Se registraron dos usuarios mediante `POST /auth/register`.
3. Se obtuvo el `user_id` del remitente.
4. Se obtuvo el `user_id` del destinatario.
5. Se envió un mensaje con `POST /messages`.
6. El sistema devolvió `ciphertext`, `nonce` y `auth_tag`.
7. Se consultaron los mensajes del destinatario con `GET /messages/{user_id}`.
8. Se obtuvo el `encrypted_key` correspondiente al destinatario.
9. Se descifró el mensaje con `POST /messages/{message_id}/decrypt`.
10. Se recuperó correctamente el plaintext original.

### Resultado validado

```json
{
  "plaintext": "Hola, este es un mensaje secreto"
}
```


## 🧪 Pruebas unitarias

Se ejecutaron pruebas unitarias para validar la funcionalidad criptográfica y de seguridad.

### Pruebas existentes

- Hashing y verificación de contraseñas.
- Generación de JWT.
- Generación de llaves RSA.
- Protección de llave privada.
- Cifrado y descifrado AES-GCM.
- Nonce único por mensaje.
- Cifrado y descifrado de clave AES con RSA-OAEP.
- Flujo híbrido individual.
- Flujo de cifrado grupal.
- Fallo de descifrado cuando se altera el `auth_tag`.
- Validación de schema de llave pública.

### Resultado

Se ejecutaron correctamente las pruebas de la carpeta `tests`.

Resultado obtenido:

```text
12 passed, 1 warning
```


## 🧪 Pruebas manuales realizadas

Además de las pruebas unitarias, se realizaron pruebas manuales usando Swagger.

### Prueba de base de datos

Endpoint utilizado:

GET `/db-test`

Resultado:

```json
{
  "message": "Conexión a PostgreSQL exitosa"
}
```

### Prueba de registro de usuarios

Endpoint utilizado:

POST `/auth/register`

Se crearon:

- Usuario Remitente
- Usuario Destinatario

### Prueba de envío de mensaje

Endpoint utilizado:

POST `/messages`

Resultado:

- Se generó un mensaje cifrado.
- El plaintext no fue almacenado ni devuelto.
- Se generaron los campos `ciphertext`, `nonce` y `auth_tag`.

### Prueba de recuperación de mensajes

Endpoint utilizado:

GET `/messages/{user_id}`

Resultado:

- Se obtuvo el mensaje cifrado del destinatario.
- Se devolvió el `encrypted_key` correspondiente al destinatario.

### Prueba de descifrado

Endpoint utilizado:

POST `/messages/{message_id}/decrypt`

Resultado:

- Se recuperó correctamente el mensaje original.
- La respuesta devolvió el plaintext esperado.


## ✅ Cumplimiento de criterios de evaluación

### Cifrado AES-256-GCM correcto con nonce único

Cumplido.

Se implementó AES-256-GCM y se validó que se genera un nonce diferente por mensaje.

### Cifrado híbrido con RSA-OAEP

Cumplido.

La clave AES efímera se cifra con la llave pública RSA del destinatario usando RSA-OAEP.

### Descifrado funcional end-to-end

Cumplido.

Se validó el flujo completo desde envío cifrado hasta recuperación del plaintext original.

### Mensajería grupal con clave compartida

Cumplido a nivel criptográfico y de diseño de almacenamiento.

El módulo de cifrado grupal genera una sola clave AES compartida y una clave cifrada por destinatario. La estructura `message_keys` permite almacenar una entrada por cada miembro del grupo.

### POST y GET de mensajes vía API REST

Cumplido.

Se implementaron:

- POST `/messages`
- GET `/messages/{user_id}`
- POST `/messages/{message_id}/decrypt`

### Pruebas unitarias del módulo

Cumplido.

Se ejecutaron pruebas unitarias del módulo, superando el mínimo requerido.


## 🧱 Archivos principales modificados o creados

### Criptografía

- `src/crypto/message_crypto.py`

### Modelos

- `src/models/message.py`
- `src/models/message_key.py`

### Persistencia

- `src/crud/message_crud.py`

### Schemas

- `src/schemas/message.py`

### API

- `src/routes/messages.py`
- `src/main.py`

### Base de datos

- `schema.sql`

### Pruebas

- `tests/test_message_crypto.py`


## ⚠️ Limitaciones actuales

Aunque el sistema cumple los requerimientos principales de la fase, existen algunas limitaciones:

- El endpoint grupal puede extenderse completamente en la capa API si se requiere una demostración directa desde Swagger.
- El descifrado se realiza en backend para fines académicos y demostrativos.
- El usuario debe proporcionar su contraseña para descifrar su llave privada.
- No se implementó todavía control de sesión con JWT para proteger endpoints de mensajes.
- No se implementaron conversaciones, historial paginado ni estados de lectura.


## 🚀 Posibles mejoras futuras

Algunas mejoras que podrían implementarse en fases posteriores son:

- Proteger endpoints de mensajes con JWT.
- Implementar `POST /messages/group` completo en API.
- Agregar conversaciones o chats.
- Agregar paginación para mensajes.
- Implementar control de permisos más estricto.
- Evitar enviar contraseñas al endpoint de descifrado, moviendo el descifrado al cliente.
- Agregar rotación de llaves.
- Agregar firmas digitales para autenticidad del remitente.
- Agregar pruebas automatizadas de endpoints con `TestClient`.


## 🏁 Conclusión

En esta fase se implementó un sistema funcional de mensajería cifrada usando cifrado híbrido. El sistema permite cifrar mensajes con AES-256-GCM, proteger la clave AES con RSA-OAEP, almacenar de forma segura el mensaje cifrado y recuperar el plaintext mediante un flujo de descifrado end-to-end.

La arquitectura con `messages` y `message_keys` permite soportar tanto mensajes individuales como mensajes grupales. Además, la integración con FastAPI permite exponer el flujo mediante endpoints REST funcionales y probados manualmente.

Con esto, el módulo de cifrado híbrido de mensajes queda implementado y listo para integrarse con futuras funcionalidades del sistema.
