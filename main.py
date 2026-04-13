import asyncio
import os
from dotenv import load_dotenv

from core.license_manager import LicenseManager
from core.database        import Database
from core.bot             import BotBase
from core.plugin_loader   import PluginLoader

load_dotenv()


async def main():
    # 1. Valida licença antes de tudo
    LicenseManager.validate()

    # 2. Conecta ao MongoDB
    Database.connect()

    # 3. Cria o bot e carrega os módulos definidos no .env
    bot    = BotBase()
    loader = PluginLoader(bot)

    modules = [m.strip() for m in os.getenv("MODULES", "").split(",") if m.strip()]

    async with bot:
        await loader.load_all(modules)
        await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
