import hmac
import hashlib
import os
import sys


class LicenseManager:
    @staticmethod
    def validate():
        client_id    = os.getenv("CLIENT_ID", "")
        license_key  = os.getenv("BOT_LICENSE_KEY", "")
        master_secret = os.getenv("MASTER_SECRET", "")

        if not all([client_id, license_key, master_secret]):
            print("[LICENÇA] Variáveis de ambiente faltando. Verifique o .env")
            sys.exit(1)

        expected = hmac.new(
            master_secret.encode(),
            client_id.encode(),
            hashlib.sha256
        ).hexdigest()[:16]

        if license_key != expected:
            print("[LICENÇA] Chave inválida. Contate o desenvolvedor.")
            sys.exit(1)

        print(f"[LICENÇA] OK — cliente: {client_id}")
        return True
