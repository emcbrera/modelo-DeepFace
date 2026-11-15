"""
Pruebas unitarias de validar_expresion_neutral con DeepFace.analyze simulado.

Uso (desde la raíz del repositorio):
    python -m unittest discover -s tests -v
"""

import io
import unittest
from unittest.mock import patch

from app.validador_expresion import (
    MENSAJE_NEUTRAL,
    MENSAJE_NO_NEUTRAL,
    UMBRAL_MAX_HAPPY,
    ErrorProcesamiento,
    validar_expresion_neutral,
)

RUTA_DEEPFACE = "app.validador_expresion.DeepFace.analyze"
MOTIVO_APROBADO = MENSAJE_NEUTRAL
EMOCIONES_RESPUESTA = {"angry", "disgusted", "fearful", "happy", "sad", "surprised", "neutral"}


def _resultado_deepface(dominante: str, happy: float, emocion_dominante: float = 70.0) -> list:
    """Construye una respuesta de DeepFace.analyze con scores en escala 0-100."""
    emociones = {
        "angry": 0.0,
        "disgust": 0.0,
        "fear": 0.0,
        "happy": happy,
        "sad": 0.0,
        "surprise": 0.0,
        "neutral": 0.0,
    }
    if dominante != "happy":
        emociones[dominante] = emocion_dominante
    resto = 100.0 - sum(emociones.values())
    emociones["sad"] += resto
    return [{"dominant_emotion": dominante, "emotion": emociones}]


class TestUmbralHappy(unittest.TestCase):
    def _validar(self, dominante: str, happy_normalizado: float) -> dict:
        resultado = _resultado_deepface(dominante, happy_normalizado * 100.0)
        with patch(RUTA_DEEPFACE, return_value=resultado):
            return validar_expresion_neutral("foto.jpg")

    def test_umbral_definido(self):
        self.assertEqual(UMBRAL_MAX_HAPPY, 0.20)

    def test_escenarios_de_aprobacion(self):
        escenarios = [
            ("neutral", 0.05, True),
            ("neutral", 0.20, True),
            ("neutral", 0.21, False),
            ("happy", 0.70, False),
            ("angry", 0.10, False),
        ]
        for dominante, happy, esperado in escenarios:
            with self.subTest(dominante=dominante, happy=happy):
                r = self._validar(dominante, happy)
                self.assertIs(r["aprobado"], esperado)
                self.assertAlmostEqual(r["detalles"]["scores"]["happy"], happy)

    def test_neutral_aprobado_usa_motivo_de_aprobacion(self):
        r = self._validar("neutral", 0.05)
        self.assertEqual(r["motivo"], MOTIVO_APROBADO)

    def test_neutral_con_happy_alto_usa_motivo_de_rechazo(self):
        r = self._validar("neutral", 0.21)
        self.assertFalse(r["aprobado"])
        self.assertEqual(r["motivo"], MENSAJE_NO_NEUTRAL)
        self.assertEqual(r["detalles"]["expresion_dominante"], "neutral")

    def test_coherencia_entre_aprobado_y_motivo(self):
        escenarios = [
            ("neutral", 0.05),
            ("neutral", 0.20),
            ("neutral", 0.21),
            ("neutral", 0.40),
            ("happy", 0.70),
            ("angry", 0.10),
            ("fear", 0.10),
        ]
        for dominante, happy in escenarios:
            with self.subTest(dominante=dominante, happy=happy):
                r = self._validar(dominante, happy)
                self.assertEqual(r["aprobado"], r["motivo"] == MOTIVO_APROBADO)

    def test_rechazo_usa_mensaje_uniforme(self):
        for dominante in ("happy", "sad", "angry", "surprise", "fear", "disgust"):
            with self.subTest(dominante=dominante):
                r = self._validar(dominante, 0.10)
                self.assertFalse(r["aprobado"])
                self.assertEqual(r["motivo"], MENSAJE_NO_NEUTRAL)

    def test_estructura_de_respuesta(self):
        r = self._validar("neutral", 0.05)
        self.assertEqual(set(r), {"aprobado", "motivo", "detalles"})
        self.assertEqual(set(r["detalles"]), {"expresion_dominante", "scores"})
        self.assertEqual(set(r["detalles"]["scores"]), EMOCIONES_RESPUESTA)
        for valor in r["detalles"]["scores"].values():
            self.assertGreaterEqual(valor, 0.0)
            self.assertLessEqual(valor, 1.0)

    def test_deepface_se_invoca_con_retinaface(self):
        resultado = _resultado_deepface("neutral", 5.0)
        with patch(RUTA_DEEPFACE, return_value=resultado) as analyze:
            validar_expresion_neutral("foto.jpg")
        analyze.assert_called_once_with(
            img_path="foto.jpg",
            actions=["emotion"],
            detector_backend="retinaface",
        )


class TestValidacionesExistentes(unittest.TestCase):
    def test_sin_rostro(self):
        error = ValueError("Face could not be detected in foto.jpg.")
        with patch(RUTA_DEEPFACE, side_effect=error):
            r = validar_expresion_neutral("foto.jpg")
        self.assertEqual(
            r,
            {
                "aprobado": False,
                "motivo": "No se detectó ningún rostro en la imagen",
                "detalles": None,
            },
        )

    def test_lista_de_resultados_vacia(self):
        with patch(RUTA_DEEPFACE, return_value=[]):
            r = validar_expresion_neutral("foto.jpg")
        self.assertEqual(
            r,
            {
                "aprobado": False,
                "motivo": "No se detectó ningún rostro en la imagen",
                "detalles": None,
            },
        )

    def test_multiples_rostros(self):
        resultado = _resultado_deepface("neutral", 5.0) * 2
        with patch(RUTA_DEEPFACE, return_value=resultado):
            r = validar_expresion_neutral("foto.jpg")
        self.assertEqual(
            r,
            {
                "aprobado": False,
                "motivo": "Se detectó más de un rostro en la imagen",
                "detalles": None,
            },
        )

    def test_value_error_distinto_lanza_error_procesamiento(self):
        with patch(RUTA_DEEPFACE, side_effect=ValueError("otro error")):
            with self.assertRaises(ErrorProcesamiento):
                validar_expresion_neutral("foto.jpg")

    def test_excepcion_inesperada_lanza_error_procesamiento(self):
        with patch(RUTA_DEEPFACE, side_effect=RuntimeError("fallo")):
            with self.assertRaises(ErrorProcesamiento):
                validar_expresion_neutral("foto.jpg")


class TestEndpoint(unittest.TestCase):
    TOKEN = "token-de-prueba"

    def setUp(self):
        patcher = patch("app.config.Config.TOKEN_API", self.TOKEN)
        patcher.start()
        self.addCleanup(patcher.stop)

        from app.main import create_app

        self.cliente = create_app().test_client()

    def _enviar(self, dominante: str, happy: float):
        resultado = _resultado_deepface(dominante, happy)
        with patch(RUTA_DEEPFACE, return_value=resultado):
            return self.cliente.post(
                "/api/v1/validar-expresion",
                headers={"Authorization": f"Bearer {self.TOKEN}"},
                data={"foto": (io.BytesIO(b"imagen"), "foto.jpg")},
                content_type="multipart/form-data",
            )

    def test_contrato_json_aprobado(self):
        respuesta = self._enviar("neutral", 5.0)
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.get_json()
        self.assertIs(cuerpo["aprobado"], True)
        self.assertEqual(cuerpo["motivo"], MOTIVO_APROBADO)
        self.assertEqual(cuerpo["detalles"]["expresion_dominante"], "neutral")
        self.assertEqual(set(cuerpo["detalles"]["scores"]), EMOCIONES_RESPUESTA)

    def test_contrato_json_neutral_rechazado_por_happy(self):
        respuesta = self._enviar("neutral", 21.0)
        self.assertEqual(respuesta.status_code, 200)
        cuerpo = respuesta.get_json()
        self.assertIs(cuerpo["aprobado"], False)
        self.assertEqual(cuerpo["motivo"], MENSAJE_NO_NEUTRAL)

    def test_sin_token_sigue_devolviendo_401(self):
        respuesta = self.cliente.post("/api/v1/validar-expresion")
        self.assertEqual(respuesta.status_code, 401)


if __name__ == "__main__":
    unittest.main()
