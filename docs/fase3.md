# Fase 3

# Persona B: Criptografía

## Responsabilidad

Persona B implementa la lógica criptográfica de la Fase 3:

- Firmar mensajes con RSA-PSS.
- Verificar firmas digitales.
- Calcular SHA-256 del plaintext.
- Calcular hashes de bloques.
- Implementar proof-of-work simplificado.

La lógica de Persona B no depende directamente de base de datos ni de endpoints. Su objetivo es dejar funciones reutilizables para que Persona A y Persona C puedan integrarlas con modelos, CRUD y API.

---

## Firmas digitales

Archivo:

```text
src/crypto/signatures.py
```

Funciones principales:

```python
hash_message_sha256(plaintext: str) -> str
sign_message_hash(private_key_pem, message_hash_hex: str) -> str
verify_message_signature(public_key_pem, message_hash_hex: str, signature_b64: str) -> bool
sign_plaintext_message(private_key_pem, plaintext: str) -> dict
verify_plaintext_message(public_key_pem, plaintext: str, signature_b64: str) -> bool
```

Contrato:

- La firma se hace sobre el `SHA-256` del plaintext.
- No se firma el ciphertext.
- `message_hash` es hexadecimal de 64 caracteres.
- `signature` se guarda en Base64.
- La verificación retorna `True` si la firma es válida y `False` si no lo es.

Flujo esperado:

```text
plaintext -> SHA-256 -> firma RSA-PSS -> signature Base64
```

---

## Blockchain utils

Archivo:

```text
src/blockchain/blockchain_utils.py
```

Funciones principales:

```python
calculate_block_hash(...)
mine_block(...)
is_valid_proof(block_hash, difficulty)
validate_block_hash(...)
```

Contrato:

- Cada bloque usa `message_hash`, que viene del SHA-256 del plaintext.
- El bloque génesis debe usar `previous_hash = "0" * 64`.
- El hash del bloque se calcula con SHA-256 usando:

```text
index + timestamp + sender_id + recipient_id + message_hash + previous_hash + nonce
```

- `block_hash` es hexadecimal de 64 caracteres.
- El proof-of-work valida que el hash empiece con ceros.
- Dificultad recomendada:
  - Producción/demo: `difficulty = 4`
  - Tests: `difficulty = 2`

---

## Uso esperado por API

Al enviar mensaje:

```text
1. API recibe plaintext.
2. API obtiene la llave privada del remitente.
3. API llama sign_plaintext_message(...).
4. API guarda message_hash y signature junto al mensaje cifrado.
5. API usa message_hash para crear el bloque en blockchain.
```

Al verificar mensaje:

```text
1. API descifra el mensaje.
2. API obtiene el plaintext.
3. API llama verify_plaintext_message(...).
4. Si retorna True, el mensaje está verificado.
5. Si retorna False, el mensaje debe marcarse como NO VERIFICADO.
```
---

## Resumen técnico

```text
Firma digital: RSA-PSS
Hash del mensaje: SHA-256 del plaintext
Formato de message_hash: hexadecimal de 64 caracteres
Formato de signature: Base64
Hash de bloque: SHA-256
Formato de block_hash: hexadecimal de 64 caracteres
Genesis previous_hash: "0" * 64
Proof-of-work demo: difficulty = 4
Proof-of-work tests: difficulty = 2
```