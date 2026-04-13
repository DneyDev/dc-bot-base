from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands

from core.database import Database


class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return Database.get()

    # ── /warn ────────────────────────────────────────────────────
    @app_commands.command(name="warn", description="Adiciona um aviso a um membro")
    @app_commands.describe(membro="Membro", motivo="Motivo do aviso")
    @app_commands.default_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, membro: discord.Member, motivo: str):
        doc = {
            "guild_id":  str(interaction.guild_id),
            "user_id":   str(membro.id),
            "motivo":    motivo,
            "data":      datetime.utcnow().isoformat(),
            "autor_id":  str(interaction.user.id),
        }
        await self.db.warns.insert_one(doc)

        total = await self.db.warns.count_documents({
            "guild_id": str(interaction.guild_id),
            "user_id":  str(membro.id),
        })

        embed = discord.Embed(title="Aviso registrado", color=0xEF9F27)
        embed.add_field(name="Membro", value=membro.mention, inline=True)
        embed.add_field(name="Total",  value=f"{total} aviso(s)", inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /warns ───────────────────────────────────────────────────
    @app_commands.command(name="warns", description="Lista os avisos de um membro")
    @app_commands.describe(membro="Membro")
    @app_commands.default_permissions(moderate_members=True)
    async def warns(self, interaction: discord.Interaction, membro: discord.Member):
        cursor = self.db.warns.find({
            "guild_id": str(interaction.guild_id),
            "user_id":  str(membro.id),
        }).sort("data", 1)

        lista = await cursor.to_list(length=20)

        if not lista:
            return await interaction.response.send_message(
                f"{membro.display_name} não tem avisos.", ephemeral=True
            )

        desc = "\n".join(
            f"**{i+1}.** {w['motivo']} — `{w['data'][:10]}`"
            for i, w in enumerate(lista)
        )
        embed = discord.Embed(
            title=f"Avisos de {membro.display_name}",
            description=desc,
            color=0xEF9F27,
        )
        await interaction.response.send_message(embed=embed)

    # ── /kick ────────────────────────────────────────────────────
    @app_commands.command(name="kick", description="Expulsa um membro do servidor")
    @app_commands.describe(membro="Membro", motivo="Motivo")
    @app_commands.default_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Sem motivo informado"):
        if not membro.is_kickable():
            return await interaction.response.send_message("Não consigo expulsar este membro.", ephemeral=True)

        await membro.kick(reason=motivo)
        embed = discord.Embed(title="Membro expulso", color=0xE24B4A)
        embed.add_field(name="Membro", value=membro.display_name, inline=True)
        embed.add_field(name="Motivo", value=motivo,              inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /limpar ──────────────────────────────────────────────────
    @app_commands.command(name="limpar", description="Apaga mensagens do canal (1-100)")
    @app_commands.describe(quantidade="Número de mensagens")
    @app_commands.default_permissions(manage_messages=True)
    async def limpar(self, interaction: discord.Interaction, quantidade: app_commands.Range[int, 1, 100] = 10):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=quantidade)
        await interaction.followup.send(f"✅ {len(deleted)} mensagem(ns) apagada(s).", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
    print("[Moderação] Cog registrada.")
