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