"""
Valida todas las fotos de una carpeta con validar_expresion_neutral y guarda
los resultados en un CSV. Pensado para pruebas locales, sin pasar por HTTP.

Uso (desde la raíz del repositorio):
    python -m scripts.validar_carpeta [carpeta_fotos] [archivo_salida.csv]

Sin argumentos valida CARPETA_POR_DEFECTO y guarda SALIDA_POR_DEFECTO.
"""

import csv
import sys
from pathlib import Path

from app.validador_expresion import validar_expresion_neutral

EXTENSIONES = {".jpg", ".jpeg", ".png"}
EMOCIONES = ["neutral", "happy", "sad", "angry", "surprised", "disgusted", "fearful"]

CARPETA_DATASET = Path(
    r"C:\Users\emcab\OneDrive - Unicamacho-academico\ING_SISTEMAS"
    r"\Trabajo de Grado\01 Analisis\Dataset\Dataset_Eimy"
)
CARPETA_POR_DEFECTO = CARPETA_DATASET / "Evaluacion"
SALIDA_POR_DEFECTO = CARPETA_DATASET / "resultados_evaluacion_deepface.csv"


def main() -> None:
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA_POR_DEFECTO
    salida = Path(sys.argv[2]) if len(sys.argv) > 2 else SALIDA_POR_DEFECTO

    if not carpeta.is_dir():
        print(f"La carpeta no existe: {carpeta}")
        sys.exit(1)

    fotos = sorted(p for p in carpeta.iterdir() if p.suffix.lower() in EXTENSIONES)
    total = len(fotos)

    with salida.open("w", newline="", encoding="utf-8-sig") as f:
        # Separador ";" y coma decimal para que Excel en español lo abra en columnas.
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            ["archivo", "aprobado", "motivo", "expresion_dominante"]
            + [f"score_{e}" for e in EMOCIONES]
        )

        for indice, ruta in enumerate(fotos, start=1):
            try:
                r = validar_expresion_neutral(str(ruta))
                detalles = r["detalles"]
                if detalles:
                    dominante = detalles["expresion_dominante"]
                    scores = [
                        f"{detalles['scores'].get(e, 0.0):.4f}".replace(".", ",")
                        for e in EMOCIONES
                    ]
                else:
                    dominante = ""
                    scores = [""] * len(EMOCIONES)
                writer.writerow([ruta.name, r["aprobado"], r["motivo"], dominante] + scores)
            except Exception as exc:
                writer.writerow([ruta.name, "", f"ERROR: {exc}", ""] + [""] * len(EMOCIONES))
            f.flush()
            print(f"[{indice}/{total}] {ruta.name}")

    print(f"Resultados guardados en {salida}")


if __name__ == "__main__":
    main()
