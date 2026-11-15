# modelo-DeepFace
Modelo DeepFace para análisis de expresiones faciales. Recibe una imagen y valida si la expresión es neutral, como parte del proceso de verificación de fotos tipo documento del proyecto SIVAF. Expone un endpoint HTTP que es consumido por el backend principal.

# Paso 1: Ubicarte en la carpeta del repositorio

# Paso 2: Crear el entorno virtual con Python 3.12
	- py -3.12 -m venv venv

# Paso 3: Activar el entorno virtual
	- venv\Scripts\actívate

# Paso 4: Confirmar que el entorno usa la versión correcta
	- python --version

# Paso 5:Instalar DeepFace
	- pip install deepface

# Paso 6: Verificar las dependencias instaladas
    - pip list

# Paso 7: Instalar dependencias desde requirements.txt (para un clon nuevo del repositorio)
	- pip install -r requirements.txt
	- Nota: requirements.txt incluye tf-keras, paquete puente obligatorio para que
	  retina-face funcione con TensorFlow 2.21 + Keras 3. Sin él, el servicio falla
	  al arrancar con: "ValueError: You have tensorflow 2.21.0 and this requires tf-keras package."

# Paso 8: Configurar las variables de entorno
	- Copiar .env.example a .env
	- Reemplazar el valor de TOKEN_API por un token real (no dejar el placeholder).
	  Se puede generar uno seguro con:
	  python -c "import secrets; print(secrets.token_urlsafe(48))"
	- El archivo .env nunca se sube a git (ver .gitignore)

# Paso 9: Ejecutar el servicio localmente

## Opción A: con Flask (desarrollo)
	- Windows (PowerShell): $env:FLASK_APP = "app.main"
	- flask --app app.main run

## Opción B: con Gunicorn (equivalente a cómo correrá en Docker)
	- gunicorn app.main:app --bind 0.0.0.0:5000

El servicio queda disponible en http://localhost:5000

# Documentación de la API

## Autenticación
Todas las peticiones deben incluir el header:

	Authorization: Bearer <TOKEN_API>

Donde `<TOKEN_API>` es el valor configurado en la variable de entorno `TOKEN_API`.
Si falta o no coincide, se responde `401 {"error": "No autorizado"}`.

## POST /api/v1/validar-expresion

Recibe una imagen tipo documento/pasaporte y valida si la expresión facial dominante es neutral.

**Request**
- Método: `POST`
- Content-Type: `multipart/form-data`
- Campo del archivo: `foto`

Ejemplo con curl:

	curl -X POST http://localhost:5000/api/v1/validar-expresion \
	  -H "Authorization: Bearer <TOKEN_API>" \
	  -F "foto=@ruta/a/la/imagen.jpg"

**Respuestas posibles**

| Situación | Código HTTP | Cuerpo |
|---|---|---|
| Expresión neutral confirmada | 200 | `{"aprobado": true, "motivo": "Expresión neutral confirmada", "detalles": {...}}` |
| Expresión no neutral (ej. sonriendo) | 200 | `{"aprobado": false, "motivo": "...", "detalles": {...}}` |
| No se detectó ningún rostro | 200 | `{"aprobado": false, "motivo": "No se detectó ningún rostro en la imagen", "detalles": null}` |
| Se detectó más de un rostro | 200 | `{"aprobado": false, "motivo": "Se detectó más de un rostro en la imagen", "detalles": null}` |
| Token faltante o incorrecto | 401 | `{"error": "No autorizado"}` |
| No se envió el campo `foto` | 400 | `{"error": "No se recibió ninguna foto"}` |
| Error interno inesperado | 500 | `{"error": "Error al procesar la imagen"}` |

El campo `detalles.scores` contiene los siete valores de emoción de DeepFace, normalizados
como fracción (0 a 1, no porcentaje): `neutral`, `happy`, `sad`, `angry`, `surprised`,
`disgusted`, `fearful`.

# Notas para el backend consumidor (Django/DRF)
	- El servicio corre en su propio contenedor Docker (Dockerfile pendiente, en un
	  paso posterior) y se consume únicamente vía HTTP.
	- El token de autenticación es estático y compartido entre ambos servicios;
	  debe coincidir con el valor de TOKEN_API configurado en este microservicio.
	- Todas las respuestas son JSON, incluso los casos de error de negocio
	  (sin rostro, expresión no neutral), que responden 200 por diseño.