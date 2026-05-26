# Demo Final — Módulo 4: Integración, MFA y Despliegue

## Objetivo de la demo

Esta demo muestra el flujo completo del sistema de mensajería cifrada, integrando:

- Registro de usuarios.
- Autenticación con password hash.
- Activación de MFA con TOTP.
- Login con password + TOTP.
- Emisión de access token y refresh token.
- Envío de mensaje cifrado y firmado.
- Verificación de firma digital.
- Descifrado del mensaje.
- Registro de la transacción en blockchain.
- Verificación de integridad de la blockchain.
- Despliegue con Docker Compose.

La demo se realiza desde Swagger UI, que funciona como interfaz básica documentada del sistema.


## 1. Levantar el proyecto con Docker

Desde la raíz del proyecto:

```bash
docker compose up --build
```

Esto levanta:

- API FastAPI.
- Base de datos PostgreSQL.
- Inicialización del esquema definido en `schema.sql`.

Abrir Swagger UI:

```text
http://127.0.0.1:8000/docs
```


## 2. Registrar Usuario A

Endpoint:

```http
POST /auth/register
```

Body:

```json
{
  "display_name": "Usuario A",
  "email": "usuarioa@example.com",
  "password": "Password123"
}
```

Guardar el `user_id` devuelto como:

```text
USER_A_ID
```


## 3. Registrar Usuario B

Endpoint:

```http
POST /auth/register
```

Body:

```json
{
  "display_name": "Usuario B",
  "email": "usuariob@example.com",
  "password": "Password123"
}
```

Guardar el `user_id` devuelto como:

```text
USER_B_ID
```


## 4. Login inicial de Usuario A sin MFA

Endpoint:

```http
POST /auth/login
```

Body:

```json
{
  "email": "usuarioa@example.com",
  "password": "Password123"
}
```

Respuesta esperada:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "mfa_required": false,
  "message": "Login exitoso"
}
```

Guardar:

```text
ACCESS_TOKEN_A
REFRESH_TOKEN_A
```


## 5. Autorizar Swagger con el access token

En Swagger UI, presionar el botón **Authorize**.

Colocar:

```text
Bearer ACCESS_TOKEN_A
```

Si Swagger agrega automáticamente el prefijo `Bearer`, colocar solo el token.

---

## 6. Activar MFA para Usuario A

Endpoint:

```http
POST /auth/mfa/enable
```

Este endpoint requiere autorización con JWT.

No requiere body.

Respuesta esperada:

```json
{
  "message": "MFA activado correctamente",
  "totp_secret": "...",
  "otpauth_url": "otpauth://..."
}
```

Guardar:

```text
TOTP_SECRET_A
```

MFA queda activo porque el campo `users.totp_secret` ya no es `null`.


## 7. Generar código TOTP

Se puede usar Google Authenticator, Authy, 2FAS o el comando siguiente:

```bash
python -c "import pyotp; print(pyotp.TOTP('TOTP_SECRET_A').now())"
```

Reemplazar `TOTP_SECRET_A` por el secreto real devuelto en el paso anterior.

El resultado será un código de 6 dígitos, por ejemplo:

```text
123456
```

Los códigos TOTP duran aproximadamente 30 segundos.


## 8. Verificar MFA manualmente

Endpoint:

```http
POST /auth/mfa/verify
```

Este endpoint requiere autorización con JWT.

Body:

```json
{
  "code": "CODIGO_TOTP"
}
```

Respuesta esperada:

```json
{
  "mfa_valid": true,
  "message": "Código TOTP válido"
}
```


## 9. Login de Usuario A sin TOTP después de activar MFA

Endpoint:

```http
POST /auth/login
```

Body:

```json
{
  "email": "usuarioa@example.com",
  "password": "Password123"
}
```

Respuesta esperada:

```json
{
  "mfa_required": true,
  "message": "MFA requerido para completar el inicio de sesión"
}
```

Esto demuestra que el sistema ya no emite tokens si MFA está activo y no se envía código TOTP.


## 10. Login de Usuario A con TOTP

Generar un código TOTP nuevo:

```bash
python -c "import pyotp; print(pyotp.TOTP('TOTP_SECRET_A').now())"
```

Endpoint:

```http
POST /auth/login
```

Body:

```json
{
  "email": "usuarioa@example.com",
  "password": "Password123",
  "totp_code": "CODIGO_TOTP"
}
```

Respuesta esperada:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer",
  "mfa_required": false,
  "message": "Login exitoso"
}
```

Guardar el nuevo:

```text
ACCESS_TOKEN_A
REFRESH_TOKEN_A
```


## 11. Probar refresh token

Endpoint:

```http
POST /auth/refresh
```

Body:

```json
{
  "refresh_token": "REFRESH_TOKEN_A"
}
```

Respuesta esperada:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Esto demuestra que el sistema puede renovar el access token usando un refresh token válido.


## 12. Usuario A envía mensaje cifrado y firmado a Usuario B

Endpoint:

```http
POST /messages
```

Body:

```json
{
  "sender_id": "USER_A_ID",
  "recipient_id": "USER_B_ID",
  "plaintext": "Mensaje final cifrado, firmado y registrado en blockchain.",
  "sender_password": "Password123"
}
```

Respuesta esperada:

```json
{
  "id": "...",
  "sender_id": "USER_A_ID",
  "recipient_id": "USER_B_ID",
  "group_id": null,
  "ciphertext": "...",
  "nonce": "...",
  "auth_tag": "...",
  "signature": "...",
  "signature_valid": null,
  "message_hash": "...",
  "created_at": "..."
}
```

Guardar:

```text
MESSAGE_ID
```

Este endpoint demuestra:

- Cifrado del mensaje con AES-256-GCM.
- Cifrado de la clave AES con RSA-OAEP usando la llave pública del destinatario.
- Firma digital del hash del mensaje usando la llave privada del remitente.
- Registro automático del `message_hash` en blockchain.


## 13. Usuario B verifica la firma del mensaje

Endpoint:

```http
POST /messages/{message_id}/verify
```

Usar:

```text
MESSAGE_ID
```

Body:

```json
{
  "user_id": "USER_B_ID",
  "password": "Password123"
}
```

Respuesta esperada:

```json
{
  "message_id": "MESSAGE_ID",
  "signature_valid": true,
  "warning": null
}
```

Este endpoint valida que:

- Usuario B tiene acceso al mensaje mediante `message_keys`.
- El mensaje puede descifrarse internamente.
- Se recalcula el SHA-256 del plaintext.
- La firma se verifica con la llave pública del remitente.
- La firma corresponde al mensaje enviado por Usuario A.


## 14. Usuario B descifra el mensaje

Endpoint:

```http
POST /messages/{message_id}/decrypt
```

Usar:

```text
MESSAGE_ID
```

Body:

```json
{
  "user_id": "USER_B_ID",
  "password": "Password123"
}
```

Respuesta esperada:

```json
{
  "message_id": "MESSAGE_ID",
  "plaintext": "Mensaje final cifrado, firmado y registrado en blockchain.",
  "signature_valid": true,
  "warning": null
}
```

Esto demuestra que solo el destinatario puede descifrar el mensaje usando su llave privada protegida por contraseña.


## 15. Consultar blockchain

Endpoint:

```http
GET /blockchain
```

Respuesta esperada:

```json
[
  {
    "id": "...",
    "index": 0,
    "timestamp": "...",
    "sender_id": "USER_A_ID",
    "recipient_id": "USER_B_ID",
    "message_hash": "...",
    "previous_hash": "0000000000000000000000000000000000000000000000000000000000000000",
    "nonce": 1234,
    "hash": "0000..."
  }
]
```

Esto demuestra que la transacción del mensaje fue registrada en blockchain.

La blockchain no guarda el plaintext ni el ciphertext del mensaje. Solo guarda el `message_hash` y datos de auditoría.


## 16. Verificar integridad de blockchain

Endpoint:

```http
GET /blockchain/verify
```

Respuesta esperada:

```json
{
  "valid": true,
  "blocks_checked": 1,
  "warning": null
}
```

Esto demuestra que:

- El hash del bloque coincide con los datos almacenados.
- El `previous_hash` es correcto.
- La cadena no ha sido alterada.


## 17. Prueba negativa opcional: TOTP inválido

Endpoint:

```http
POST /auth/login
```

Body:

```json
{
  "email": "usuarioa@example.com",
  "password": "Password123",
  "totp_code": "000000"
}
```

Respuesta esperada:

```json
{
  "detail": "Código TOTP inválido"
}
```

Esto demuestra que MFA rechaza códigos incorrectos.


## 18. Prueba negativa opcional: usuario sin permiso intenta verificar mensaje

Crear un Usuario C:

```http
POST /auth/register
```

Body:

```json
{
  "display_name": "Usuario C",
  "email": "usuarioc@example.com",
  "password": "Password123"
}
```

Intentar verificar el mensaje de A hacia B:

```http
POST /messages/{message_id}/verify
```

Body:

```json
{
  "user_id": "USER_C_ID",
  "password": "Password123"
}
```

Respuesta esperada:

```json
{
  "detail": "El usuario no tiene permiso para verificar este mensaje"
}
```

Esto demuestra que conocer el `message_id` no basta para verificar un mensaje ajeno.


## 19. Prueba negativa opcional: romper blockchain

Entrar a PostgreSQL:

```bash
docker exec -it proyecto2_postgres psql -U postgres -d proyecto2
```

Modificar un bloque:

```sql
UPDATE blockchain
SET message_hash = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
WHERE index = 0;
```

Luego ejecutar:

```http
GET /blockchain/verify
```

Respuesta esperada:

```json
{
  "valid": false,
  "blocks_checked": 1,
  "warning": "El bloque 0 tiene un hash inválido o no cumple proof-of-work."
}
```

Esto demuestra que la blockchain detecta alteraciones.


## Resumen de endpoints usados

```http
POST /auth/register
POST /auth/login
POST /auth/mfa/enable
POST /auth/mfa/verify
POST /auth/refresh
POST /messages
POST /messages/{message_id}/verify
POST /messages/{message_id}/decrypt
GET /blockchain
GET /blockchain/verify
```


## Resultado esperado final

Al completar la demo, se demuestra el flujo completo:

```text
Registro
→ MFA
→ Login con password + TOTP
→ Access token + refresh token
→ Envío de mensaje cifrado y firmado
→ Verificación de firma
→ Descifrado
→ Registro en blockchain
→ Verificación de integridad de blockchain
→ Despliegue con Docker
```