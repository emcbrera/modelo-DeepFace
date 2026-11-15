import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    TOKEN_API = os.environ.get("TOKEN_API")

    @classmethod
    def validar(cls):
        if not cls.TOKEN_API:
            raise RuntimeError(
                "La variable de entorno TOKEN_API no está definida. "
                "Configúrala en el archivo .env antes de iniciar el servicio."
            )


Config.validar()
