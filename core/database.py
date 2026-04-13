import os
import motor.motor_asyncio


class Database:
    _client = None
    _db     = None

    @classmethod
    def connect(cls):
        uri  = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        name = os.getenv("MONGO_DB",  "discord_bot")

        cls._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        cls._db     = cls._client[name]
        print(f"[DB] Conectado ao MongoDB — banco: {name}")

    @classmethod
    def get(cls):
        if cls._db is None:
            raise RuntimeError("Banco não conectado. Chame Database.connect() primeiro.")
        return cls._db

    @classmethod
    def close(cls):
        if cls._client:
            cls._client.close()
            print("[DB] Conexão encerrada.")
