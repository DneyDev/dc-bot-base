import random
import re
import discord
from discord import app_commands
from discord.ext import commands

from core.database import Database


def rolar_dado(lados: int) -> int:
    return random.randint(1, lados)


def parse_dado(texto: str):
    """Aceita: d20, 2d6, 1d8. Retorna (qtd, lados) ou None."""
    match = re.fullmatch(r"(\d*)d(\d+)", texto.lower())
    if not match:
        return None
    qtd   = int(match.group(1)) if match.group(1) else 1
    lados = int(match.group(2))
    if not (1 <= qtd <= 20 and lados >= 2):
        return None
    return qtd, lados


class RPGCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @property
    def db(self):
        return Database.get()

    # ── /rolar ──────────────────────────────────────────────────
    @app_commands.command(name="rolar", description="Rola um ou mais dados. Ex: d20, 2d6")
    @app_commands.describe(dado="Formato: d20, 2d6, 1d8", motivo="Motivo da rolagem (opcional)")
    async def rolar(self, interaction: discord.Interaction, dado: str, motivo: str = None):
        parsed = parse_dado(dado)
        if not parsed:
            return await interaction.response.send_message(
                "Formato inválido. Use: `d20`, `2d6`, `1d8`...", ephemeral=True
            )

        qtd, lados = parsed
        resultados = [rolar_dado(lados) for _ in range(qtd)]
        total      = sum(resultados)

        desc = None
        if total == lados * qtd:
            desc = "Crítico!"
        elif total == qtd and lados >= 20:
            desc = "Falha crítica!"

        embed = discord.Embed(title=f"🎲 {qtd}d{lados}", color=0x7F77DD, description=desc)
        embed.add_field(name="Resultados", value=" + ".join(map(str, resultados)), inline=True)
        embed.add_field(name="Total",      value=f"**{total}**",                  inline=True)
        embed.set_footer(text=f"Motivo: {motivo}" if motivo else f"Rolado por {interaction.user.name}")

        await interaction.response.send_message(embed=embed)

    # ── /ficha criar ────────────────────────────────────────────
    @app_commands.command(name="ficha_criar", description="Cria sua ficha de personagem")
    @app_commands.describe(nome="Nome do personagem", classe="Classe (ex: Guerreiro, Mago)", nivel="Nível 1-20")
    async def ficha_criar(self, interaction: discord.Interaction, nome: str, classe: str, nivel: int):
        if not 1 <= nivel <= 20:
            return await interaction.response.send_message("Nível deve ser entre 1 e 20.", ephemeral=True)

        ficha = {
            "user_id":  str(interaction.user.id),
            "guild_id": str(interaction.guild_id),
            "nome":     nome,
            "classe":   classe,
            "nivel":    nivel,
            "hp":       nivel * 10,
            "xp":       0,
        }

        await self.db.fichas.replace_one(
            {"user_id": ficha["user_id"], "guild_id": ficha["guild_id"]},
            ficha,
            upsert=True,
        )

        embed = discord.Embed(title="Ficha criada!", color=0x1D9E75)
        embed.add_field(name="Nome",   value=nome,          inline=True)
        embed.add_field(name="Classe", value=classe,        inline=True)
        embed.add_field(name="Nível",  value=str(nivel),    inline=True)
        embed.add_field(name="HP",     value=str(nivel*10), inline=True)
        embed.add_field(name="XP",     value="0",           inline=True)
        await interaction.response.send_message(embed=embed)

    # ── /ficha ver ──────────────────────────────────────────────
    @app_commands.command(name="ficha_ver", description="Exibe sua ficha de personagem")
    async def ficha_ver(self, interaction: discord.Interaction):
        ficha = await self.db.fichas.find_one({
            "user_id":  str(interaction.user.id),
            "guild_id": str(interaction.guild_id),
        })

        if not ficha:
            return await interaction.response.send_message(
                "Você não tem ficha. Use `/ficha_criar` primeiro.", ephemeral=True
            )

        embed = discord.Embed(title=f"📜 {ficha['nome']}", color=0x7F77DD)
        embed.add_field(name="Classe", value=ficha["classe"],       inline=True)
        embed.add_field(name="Nível",  value=str(ficha["nivel"]),   inline=True)
        embed.add_field(name="HP",     value=str(ficha["hp"]),      inline=True)
        embed.add_field(name="XP",     value=str(ficha["xp"]),      inline=True)
        await interaction.response.send_message(embed=embed)

    # ── /iniciativa ─────────────────────────────────────────────
    @app_commands.command(name="iniciativa", description="Rola iniciativa para o combate")
    @app_commands.describe(personagens="Nomes separados por vírgula: Aragorn, Orc, Gandalf")
    async def iniciativa(self, interaction: discord.Interaction, personagens: str):
        nomes = [n.strip() for n in personagens.split(",") if n.strip()]
        if not nomes:
            return await interaction.response.send_message("Informe pelo menos um personagem.", ephemeral=True)

        rolls = sorted(
            [{"nome": n, "roll": rolar_dado(20)} for n in nomes],
            key=lambda x: x["roll"],
            reverse=True,
        )

        lista = "\n".join(f"**{i+1}.** {r['nome']} — `{r['roll']}`" for i, r in enumerate(rolls))
        embed = discord.Embed(title="⚔️ Ordem de iniciativa", description=lista, color=0xD85A30)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(RPGCog(bot))
    print("[RPG] Cog registrada.")
