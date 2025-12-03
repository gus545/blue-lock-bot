import discord
from discord import app_commands
from discord.ext import commands
import os
from utils.formatting import create_game_embed, create_stat_embed
from main import LeagueBot




API_URL = os.getenv("API_URL", "http://localhost:8000")


class Teams(commands.Cog):
    def __init__(self, bot:  LeagueBot):
        self.bot = bot

    @app_commands.command(name="stats", description="Get stats for a team")
    async def stats(self, interaction: discord.Interaction, team_id: int = None):
        await interaction.response.defer()

        team_data = await self.bot.api.get_team_from_id(team_id=team_id)

        if not team_data:
            await interaction.followup.send("No team found", ephemeral=True)
            return

        embed = create_stat_embed(team_data, title = f"Stats for team {team_data.get('name','N/A')}")
        await interaction.followup.send(embed=embed)





async def setup(bot):
    await bot.add_cog(Teams(bot))