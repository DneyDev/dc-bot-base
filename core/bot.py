import discord
from discord.ext import commands


class BotBase(commands.Bot):
    """
    Subclasse de commands.Bot com setup personalizado.
    Todos os módulos (Cogs) são carregados pelo PluginLoader.
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix="!",       # prefixo legado (opcional, usamos slash commands)
            intents=intents,
            help_command=None,        # desativa o !help padrão
        )

    async def on_ready(self):
        # Sincroniza slash commands com o Discord
        synced = await self.tree.sync()
        print(f"[Bot] Online como {self.user} — {len(synced)} comando(s) sincronizado(s).")

    async def on_command_error(self, ctx, error):
        print(f"[Bot] Erro: {error}")
