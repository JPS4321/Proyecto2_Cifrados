# 🔐 Módulo de Criptografía — Persona B

## 📌 Descripción general

En esta fase se implementó el módulo criptográfico encargado de garantizar la protección de las llaves privadas de los usuarios dentro del sistema.

Este módulo cubre:

- Generación de pares de llaves RSA-2048  
- Derivación de claves seguras a partir de contraseñas  
- Cifrado de la llave privada utilizando AES-256-GCM  
- Preparación de los datos para su almacenamiento seguro  

El objetivo principal es asegurar que la llave privada nunca sea almacenada en texto plano.

---

## 🔑 Generación de par de llaves

Se implementó la función:

```python
generate_rsa_keypair()
```

Esta función genera:

- Llave privada en formato PEM  
- Llave pública en formato PEM  

Se utiliza el algoritmo RSA con un tamaño de clave de 2048 bits, cumpliendo con los requerimientos del proyecto.

---

## 🔐 Derivación de clave

Se utiliza PBKDF2 con HMAC-SHA256 para derivar una clave segura a partir de la contraseña del usuario.

Características:

- Uso de `salt` aleatorio  
- Número elevado de iteraciones (390000)  
- Generación de una clave de 256 bits  

Esto protege contra ataques de fuerza bruta y ataques de diccionario.

---

## 🔒 Cifrado de la llave privada

Se implementó la función:

```python
encrypt_private_key(private_key, password)
```

### Proceso:

1. Se genera un `salt` aleatorio  
2. Se deriva una clave con PBKDF2  
3. Se genera un `nonce`  
4. Se cifra la llave privada con AES-256-GCM  

### Salida:

```json
{
  "kdf": "PBKDF2-HMAC-SHA256",
  "iterations": 390000,
  "salt": "...",
  "nonce": "...",
  "ciphertext": "..."
}
```

**Nota importante:**

El tag de autenticación de AES-GCM está incluido dentro del campo `ciphertext`.

---

## 🔄 Función principal de integración

Se implementó la función:

```python
generate_and_protect_keypair(password)
```

Esta función:

1. Genera el par de llaves RSA  
2. Cifra la llave privada  
3. Retorna los valores listos para almacenar  

### Uso:

```python
public_key, encrypted_private_key = generate_and_protect_keypair(password)
```

---

## 🧩 Integración con el registro de usuario

Durante el proceso de registro:

- `public_key` → se almacena en la columna `public_key`  
- `encrypted_private_key` → se almacena en la columna `encrypted_private_key`  

El campo `encrypted_private_key` se guarda como un string JSON.

---

## 🧪 Pruebas unitarias

Se implementaron pruebas en:

```
tests/test_crypto.py
```

Se validó:

- Generación correcta del par de llaves  
- Cifrado de la llave privada  
- Descifrado correcto con la misma contraseña  

### Resultado:

```
3 tests passed
```

---

## ✅ Cumplimiento de requisitos

Este módulo cumple con los siguientes requerimientos del proyecto:

- Generación de par de llaves RSA-2048  
- Protección de la llave privada mediante clave derivada (PBKDF2)  
- Uso de cifrado autenticado (AES-GCM)  
- Preparación de datos para almacenamiento seguro  

---

# 🔑 Módulo de Autenticación y API — Persona C

## 📌 Descripción general

En esta fase se implementó el módulo de autenticación y la capa de API del sistema, encargado de gestionar el registro de usuarios, el inicio de sesión y la exposición de endpoints para el consumo de datos.

Este módulo integra los componentes desarrollados por:

- Persona A → persistencia y base de datos  
- Persona B → criptografía (generación y protección de llaves)  

El objetivo principal es proporcionar una interfaz segura y funcional para la interacción con el sistema.

---

## 🔐 Hashing de contraseñas

Se implementó el manejo seguro de contraseñas utilizando el algoritmo bcrypt mediante la librería `passlib`.

Funciones implementadas:

```python
hash_password(password)
verify_password(plain_password, hashed_password)
```

### Características:

- Las contraseñas nunca se almacenan en texto plano  
- Se utiliza hashing con salt automático  
- Comparación segura de contraseñas durante el login  

---

## 🎟️ Generación y verificación de JWT

Se implementó autenticación basada en JSON Web Tokens (JWT) para manejar sesiones de usuario.

Funciones implementadas:

```python
create_access_token(data)
verify_token(token)
```

### Características:

- Tokens firmados con HMAC-SHA256  
- Inclusión de campo de expiración (`exp`)  
- Validación de firma e integridad del token  

---

## 👤 Endpoint de registro

Se implementó el endpoint:

```python
POST /auth/register
```

### Proceso:

1. Validación de datos de entrada  
2. Verificación de que el email no exista  
3. Hashing de la contraseña  
4. Generación del par de llaves  
5. Cifrado de la llave privada  
6. Almacenamiento del usuario  

### Resultado:

```python
{
  "message": "Usuario registrado exitosamente",
  "user_id": "...",
  "email": "...",
  "display_name": "..."
}
```

---

## 🔑 Endpoint de login

Se implementó el endpoint:

```python
POST /auth/login
```

### Proceso:

1. Búsqueda del usuario por email  
2. Verificación de contraseña  
3. Generación de token JWT  

### Resultado:

```python
{
  "access_token": "...",
  "token_type": "bearer"
}
```

---

## 🔓 Endpoint de llave pública

Se implementó el endpoint:

```python
GET /users/{id}/key
```

### Proceso:

1. Búsqueda del usuario  
2. Obtención de la llave pública  

### Resultado:

```python
{
  "user_id": "...",
  "email": "...",
  "public_key": "-----BEGIN PUBLIC KEY-----..."
}
```

---

## 🧪 Pruebas unitarias

Se implementaron pruebas en:

- tests/test_auth.py  
- tests/test_users.py  

### Validaciones realizadas:

- Hashing de contraseñas  
- Verificación de contraseñas  
- Creación y validación de JWT  
- Estructura de respuesta de llave pública  

### Resultado:

Tests ejecutados correctamente.

---

## 🧩 Integración del sistema

La aplicación se estructuró de forma modular:

- src/main.py → aplicación principal  
- main.py → punto de entrada  
- routes/ → endpoints  
- schemas/ → validación  
- core/ → seguridad  

Se utilizó FastAPI como framework principal.

---

## ✅ Cumplimiento de requisitos

Este módulo cumple con:

- Registro con hashing seguro  
- Login con JWT  
- Endpoint de llave pública  
- Integración con criptografía  