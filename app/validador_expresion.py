from deepface import DeepFace

MAPEO_EMOCIONES = {
    "angry": "angry",
    "disgust": "disgusted",
    "fear": "fearful",
    "happy": "happy",
    "sad": "sad",
    "surprise": "surprised",
    "neutral": "neutral",
}

UMBRAL_MAX_HAPPY = 0.20

MENSAJE_NO_NEUTRAL = (
    "No se detectó una expresión facial neutra. "
    "La fotografía no cumple con el requisito de expresión facial."
)

MENSAJE_NEUTRAL = "Expresión neutral confirmada"


class ErrorProcesamiento(Exception):
    """Error inesperado al analizar la imagen con DeepFace."""


def _convertir_scores(emociones_crudas: dict) -> dict:
    return {
        MAPEO_EMOCIONES.get(clave, clave): float(valor) / 100.0
        for clave, valor in emociones_crudas.items()
    }


def validar_expresion_neutral(ruta_imagen: str) -> dict:
    """
    Analiza la imagen ubicada en ruta_imagen y determina si la expresión
    facial es neutral, según las reglas de negocio de SIVAF.

    La fotografía se aprueba solo si la expresión dominante es neutral y la
    puntuación normalizada de happy (escala 0-1) es menor o igual a
    UMBRAL_MAX_HAPPY (0.20). Las puntuaciones no son probabilidades calibradas.

    Devuelve siempre un dict con la forma {aprobado, motivo, detalles},
    incluyendo los casos de negocio "sin rostro" y "múltiples rostros".

    Lanza ErrorProcesamiento si ocurre un fallo inesperado (no relacionado
    con la ausencia de un rostro) durante el análisis.
    """
    try:
        resultados = DeepFace.analyze(
            img_path=ruta_imagen,
            actions=["emotion"],
            detector_backend="retinaface",
        )
    except ValueError as exc:
        if "face could not be detected" in str(exc).lower():
            return {
                "aprobado": False,
                "motivo": "No se detectó ningún rostro en la imagen",
                "detalles": None,
            }
        raise ErrorProcesamiento(str(exc)) from exc
    except Exception as exc:
        raise ErrorProcesamiento(str(exc)) from exc

    if not resultados:
        return {
            "aprobado": False,
            "motivo": "No se detectó ningún rostro en la imagen",
            "detalles": None,
        }

    if len(resultados) > 1:
        return {
            "aprobado": False,
            "motivo": "Se detectó más de un rostro en la imagen",
            "detalles": None,
        }

    emociones_crudas = resultados[0]["emotion"]
    expresion_dominante = MAPEO_EMOCIONES.get(
        resultados[0]["dominant_emotion"], resultados[0]["dominant_emotion"]
    )

    scores = _convertir_scores(emociones_crudas)

    aprobado = (
        expresion_dominante == "neutral"
        and scores["happy"] <= UMBRAL_MAX_HAPPY
    )

    if aprobado:
        motivo = MENSAJE_NEUTRAL
    else:
        motivo = MENSAJE_NO_NEUTRAL

    return {
        "aprobado": aprobado,
        "motivo": motivo,
        "detalles": {
            "expresion_dominante": expresion_dominante,
            "scores": scores,
        },
    }
