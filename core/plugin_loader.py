import importlib
import os


class PluginLoader:
    def __init__(self, bot):
        self.bot     = bot
        self.loaded  = []

    async def load(self, module_name: str):
        """
        Carrega um módulo da pasta modules/.
        Cada módulo deve expor uma função setup(bot) — padrão do discord.py Cogs.
        """
        if module_name in self.loaded:
            print(f"[Plugin] '{module_name}' já está carregado.")
            return

        try:
            await self.bot.load_extension(f"modules.{module_name}.cog")
            self.loaded.append(module_name)
            print(f"[Plugin] '{module_name}' carregado.")
        except Exception as e:
            print(f"[Plugin] Falha ao carregar '{module_name}': {e}")

    async def load_all(self, modules: list[str]):
        for mod in modules:
            await self.load(mod)

    async def unload(self, module_name: str):
        try:
            await self.bot.unload_extension(f"modules.{module_name}.cog")
            self.loaded.remove(module_name)
            print(f"[Plugin] '{module_name}' descarregado.")
        except Exception as e:
            print(f"[Plugin] Falha ao descarregar '{module_name}': {e}")
