# Fase 4 — Trabajo realizado por Persona B

## Rol asignado

En esta fase, la Persona B se encargó principalmente del componente de seguridad relacionado con autenticación multifactor, manejo de tokens y soporte criptográfico para la integración final del sistema.

El trabajo se enfocó en complementar la autenticación existente con TOTP y refresh tokens, preparando las funciones necesarias para que la Persona C pueda integrarlas posteriormente en los endpoints de la API.

## Objetivo de la implementación

El objetivo principal fue apoyar el Entregable 4 del proyecto, correspondiente a:

- Integración final del sistema.
- Autenticación multifactor con TOTP.
- Manejo de tokens JWT.
- Preparación del flujo de sesión con access token y refresh token.
- Pruebas unitarias para validar el comportamiento de MFA y tokens.

## Archivos modificados o agregados

### Archivos agregados

```text
src/crypto/totp_utils.py
tests/test_totp_utils.py
tests/test_jwt_refresh.py
```

### Archivos modificados

```text
requirements.txt
src/core/jwt_utils.py
src/schemas/auth.py
```

## Implementación de TOTP para MFA

Se agregó el archivo:

```text
src/crypto/totp_utils.py
```

En este archivo se implementaron utilidades para autenticación multifactor basada en TOTP.

Las funciones agregadas fueron:

```python
generate_totp_secret()
```

Esta función genera un secreto Base32 para cada usuario. Este secreto será almacenado posteriormente en el campo `totp_secret` del usuario y será utilizado para generar códigos temporales compatibles con aplicaciones como Google Authenticator.

```python
build_totp_uri(email, secret)
```

Esta función genera una URI en formato `otpauth://`, la cual puede ser usada por una aplicación autenticadora o convertida en código QR durante la activación de MFA.

```python
verify_totp_code(secret, code)
```

Esta función verifica que el código TOTP ingresado por el usuario sea válido. También valida que el código tenga el formato correcto, es decir, que sea numérico y de 6 dígitos.

## Actualización de dependencias

Se agregó la dependencia:

```text
pyotp
```

Esta librería permite generar secretos TOTP, construir URIs compatibles con apps autenticadoras y verificar códigos temporales.

## Implementación de refresh tokens

Se modificó el archivo:

```text
src/core/jwt_utils.py
```

Se agregaron funciones para manejar refresh tokens y diferenciar correctamente entre tokens de acceso y tokens de refresco.

Las funciones agregadas fueron:

```python
create_refresh_token()
```

Crea un refresh token JWT con una expiración más larga que la del access token. Este token se usará para solicitar nuevos access tokens sin obligar al usuario a iniciar sesión nuevamente.

```python
verify_access_token()
```

Verifica que un token sea válido y que además sea de tipo `access`. Esto evita que un refresh token pueda usarse para acceder directamente a endpoints protegidos.

```python
verify_refresh_token()
```

Verifica que un token sea válido y que además sea de tipo `refresh`. Esto permite usarlo únicamente en el flujo de renovación de tokens.

También se actualizó la creación de access tokens para incluir el campo:

```json
"type": "access"
```

Y los refresh tokens incluyen:

```json
"type": "refresh"
```

Esto permite distinguir claramente el propósito de cada token.

## Actualización de schemas

Se modificó el archivo:

```text
src/schemas/auth.py
```

Se agregó el schema:

```python
class RefreshTokenRequest(BaseModel):
    refresh_token: str
```

Este schema será utilizado posteriormente por el endpoint de renovación de token, por ejemplo:

```http
POST /auth/refresh
```

También se dejó preparada la estructura para que la API pueda integrar el flujo de refresh token y MFA.

## Pruebas unitarias agregadas

Se agregó el archivo:

```text
tests/test_totp_utils.py
```

Este archivo valida:

- Que se genere un secreto TOTP válido.
- Que se genere correctamente una URI `otpauth://`.
- Que un código TOTP válido sea aceptado.
- Que un código incorrecto sea rechazado.
- Que formatos inválidos sean rechazados.

También se agregó el archivo:

```text
tests/test_jwt_refresh.py
```

Este archivo valida:

- Que se pueda crear y verificar un access token.
- Que se pueda crear y verificar un refresh token.
- Que un refresh token no pueda usarse como access token.
- Que un access token no pueda usarse como refresh token.

## Resultado de pruebas

Se ejecutaron las pruebas específicas de Persona B con el siguiente comando:

```bash
pytest -v tests/test_totp_utils.py tests/test_jwt_refresh.py
```

Resultado obtenido:

```text
9 passed
```

Esto confirma que las utilidades TOTP y la lógica de refresh tokens funcionan correctamente a nivel unitario.

## Commits realizados

Los cambios se organizaron en commits separados para mantener claridad en el historial del repositorio.

### Commit 1

```bash
git commit -m "feat(auth): add TOTP MFA utilities"
```

Incluye:

- Utilidades TOTP.
- Dependencia `pyotp`.
- Pruebas unitarias de TOTP.

### Commit 2

```bash
git commit -m "feat(auth): add refresh token support"
```

Incluye:

- Creación de refresh tokens.
- Verificación separada de access tokens y refresh tokens.
- Pruebas unitarias de JWT refresh.

### Commit 3

```bash
git commit -m "feat(auth): extend auth schemas for MFA and refresh tokens"
```

Incluye:

- Schema para solicitudes con refresh token.
- Preparación de schemas para integración con endpoints.

### Commit 4

```bash
git commit -m "docs(auth): document JWT refresh token helpers"
```

Incluye:

- Comentarios y documentación interna para las funciones relacionadas con refresh tokens.

## Pendientes para integración con otras personas

La implementación de Persona B deja listas las funciones de seguridad, pero todavía deben ser conectadas por las demás partes del equipo.

### Pendiente con Persona A

Coordinar el uso de variables de entorno para valores sensibles como:

```text
JWT_SECRET_KEY
```

Actualmente la clave secreta de JWT debe moverse a configuración mediante `.env` o variables de entorno para la entrega final con Docker.

### Pendiente con Persona C

Persona C debe integrar estas funciones en los endpoints correspondientes:

```http
POST /auth/mfa/enable
POST /auth/mfa/verify
POST /auth/login
POST /auth/refresh
```

También debe conectar el flujo de login para que:

- Si el usuario no tiene MFA activo, se emitan tokens normalmente.
- Si el usuario tiene MFA activo, se solicite código TOTP.
- Si el código TOTP es correcto, se emitan access token y refresh token.
- Si el código TOTP es incorrecto, se rechace el login.

## Conclusión

La Persona B completó el soporte criptográfico necesario para la fase final relacionado con MFA y tokens JWT. Se implementaron utilidades TOTP compatibles con aplicaciones autenticadoras, se agregó soporte para refresh tokens y se validó el comportamiento mediante pruebas unitarias.

Esta parte queda lista para ser integrada por la Persona C en los endpoints de autenticación y por la Persona A en la configuración final de base de datos, variables de entorno y Docker.