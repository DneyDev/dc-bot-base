import discord
from discord import app_commands
from discord.ext import commands

from core.database import Database


XP_POR_MSG = 5

CONQUISTAS = [
    {"id": "primeiro_nivel", "nome": "Primeiro passo",  "desc": "Chegou ao nível 2",  "nivel": 2},
    {"id": "nivel_cinco",    "nome": "Em evolução",      "desc": "Chegou ao nível 5",  "nivel": 5},
    {"id": "nivel_dez",      "nome": "Veterano",         "desc": "Chegou ao nível 10", "nivel": 10},
]


def xp_para_nivel(nivel: int) -> int:
    return nivel * 100


def calcular_nivel(xp_total: int) -> tuple[int, int]:
    """Retorna (nivel_atual, xp_restante_no_nivel)."""
    nivel = 1
    xp    = xp_total
    while xp >= xp_para_nivel(nivel):
        xp -= xp_para_nivel(nivel)
        nivel += 1
    return nivel, xp


class GamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def db(self):
        return Database.get()

    async def _get_player(self, user_id: str, guild_id: str) -> dict:
        player = await self.db.players.find_one({"user_id": user_id, "guild_id": guild_id})
        if not player:
            player = {"user_id": user_id, "guild_id": guild_id, "xp_total": 0, "conquistas": []}
            await self.db.players.insert_one(player)
        return player

    async def _add_xp(self, user_id: str, guild_id: str, xp: int) -> tuple[dict, list]:
        """Adiciona XP e retorna (player_atualizado, novas_conquistas)."""
        player      = await self._get_player(user_id, guild_id)
        novo_xp     = player["xp_total"] + xp
        nivel, _    = calcular_nivel(novo_xp)

        novas = []
        conquistas = player.get("conquistas", [])
        for c in CONQUISTAS:
            if c["id"] not in conquistas and nivel >= c["nivel"]:
                conquistas.append(c["id"])
                novas.append(c)

        await self.db.players.update_one(
            {"user_id": user_id, "guild_id": guild_id},
            {"$set": {"xp_total": novo_xp, "conquistas": conquistas}},
        )

        player["xp_total"]    = novo_xp
        player["conquistas"]  = conquistas
        return player, novas

    # ── /perfil ──────────────────────────────────────────────────
    @app_commands.command(name="perfil", description="Exibe seu perfil de jogador")
    @app_commands.describe(usuario="Ver perfil de outro usuário")
    async def perfil(self, interaction: discord.Interaction, usuario: discord.Member = None):
        alvo   = usuario or interaction.user
        player = await self._get_player(str(alvo.id), str(interaction.guild_id))

        nivel, xp_nivel = calcular_nivel(player["xp_total"])
        prox_xp         = xp_para_nivel(nivel)
        barras          = int((xp_nivel / prox_xp) * 10)
        barra           = "█" * barras + "░" * (10 - barras)

        conquistas_ids  = player.get("conquistas", [])
        conquistas_txt  = "\n".join(
            f"🏅 {c['nome']}" for c in CONQUISTAS if c["id"] in conquistas_ids
        ) or "Nenhuma ainda"

        embed = discord.Embed(title=f"Perfil de {alvo.display_name}", color=0x534AB7)
        embed.set_thumbnail(url=alvo.display_avatar.url)
        embed.add_field(name="Nível",     value=str(nivel),                    inline=True)
        embed.add_field(name="XP",        value=f"{xp_nivel} / {prox_xp}",     inline=True)
        embed.add_field(name="Progresso", value=f"`{barra}`",                   inline=False)
        embed.add_field(name="Conquistas",value=conquistas_txt,                 inline=False)
        await interaction.response.send_message(embed=embed)

    # ── /ranking ─────────────────────────────────────────────────
    @app_commands.command(name="ranking", description="Top 10 jogadores do servidor")
    async def ranking(self, interaction: discord.Interaction):
        cursor = self.db.players.find(
            {"guild_id": str(interaction.guild_id)}
        ).sort("xp_total", -1).limit(10)

        lista = await cursor.to_list(length=10)

        if not lista:
            return await interaction.response.send_message("Nenhum jogador no ranking ainda.", ephemeral=True)

        medals = ["🥇", "🥈", "🥉"]
        linhas = []
        for i, p in enumerate(lista):
            nivel, _ = calcular_nivel(p["xp_total"])
            medalha  = medals[i] if i < 3 else f"**{i+1}.**"
            linhas.append(f"{medalha} <@{p['user_id']}> — Nível {nivel} ({p['xp_total']} XP)")

        embed = discord.Embed(
            title="Ranking do servidor",
            description="\n".join(linhas),
            color=0x1D9E75,
        )
        await interaction.response.send_message(embed=embed)

    # ── /darxp ───────────────────────────────────────────────────
    @app_commands.command(name="darxp", description="Concede XP a um membro (admin)")
    @app_commands.describe(membro="Membro", quantidade="Quantidade de XP")
    @app_commands.default_permissions(manage_guild=True)
    async def darxp(self, interaction: discord.Interaction, membro: discord.Member, quantidade: app_commands.Range[int, 1, 10000]):
        player, novas = await self._add_xp(str(membro.id), str(interaction.guild_id), quantidade)
        nivel, _      = calcular_nivel(player["xp_total"])

        msg = f"✅ +{quantidade} XP para {membro.mention}. Agora no nível **{nivel}**."
        if novas:
            nomes = ", ".join(c["nome"] for c in novas)
            msg  += f"\n🏅 Conquista desbloqueada: **{nomes}**"

        await interaction.response.send_message(msg)

    # ── XP por mensagem (evento) ──────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        _, novas = await self._add_xp(str(message.author.id), str(message.guild.id), XP_POR_MSG)

        if novas:
            nomes = ", ".join(c["nome"] for c in novas)
            await message.channel.send(
                f"🏅 Parabéns {message.author.mention}! Conquista desbloqueada: **{nomes}**"
            )


async def setup(bot):
    await bot.add_cog(GamesCog(bot))
    print("[Games] Cog registrada.")
