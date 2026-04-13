#!/usr/bin/env python3
"""
Uso:
    python scripts/gerar_licenca.py <client_id> <modulos>

Exemplo:
    python scripts/gerar_licenca.py joao-rpg-2025 rpg,moderation
"""

import sys
import hmac
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

def gerar(client_id: str, modulos: str = "rpg"):
    master_secret = os.getenv("MASTER_SECRET")
    if not master_secret:
        print("MASTER_SECRET não definido no .env")
        sys.exit(1)

    key = hmac.new(
        master_secret.encode(),
        client_id.encode(),
        hashlib.sha256
    ).hexdigest()[:16]

    print("\n========== .env do cliente ==========")
    print(f"DISCORD_TOKEN=     # Token do bot (Discord Developer Portal)")
    print(f"CLIENT_ID={client_id}")
    print(f"BOT_LICENSE_KEY={key}")
    print(f"MASTER_SECRET={master_secret}")
    print(f"MODULES={modulos}")
    print(f"MONGO_URI=mongodb://localhost:27017")
    print(f"MONGO_DB=discord_bot")
    print("=====================================\n")
    print("Cole esse bloco no .env do cliente.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    client_id = sys.argv[1]
    modulos   = sys.argv[2] if len(sys.argv) > 2 else "rpg"
    gerar(client_id, modulos)
