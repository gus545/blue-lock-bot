import discord
from discord import app_commands
from discord.ext import commands
import os
from utils.formatting import create_game_embed
from  main import LeagueBot


API_URL = os.getenv("API_URL", "http://localhost:8000")


class Games(commands.Cog):
    def __init__(self, bot : LeagueBot):
        self.bot = bot

    @app_commands.command(name="latest", description="Get most recent completed games")
    async def latest_games(self, interaction: discord.Interaction, team_id: int = None, limit : int = 5):
        await interaction.response.defer()

        games_data = await self.bot.api.get_latest_games(team_id=team_id, limit=limit)

        if not games_data:
            await interaction.followup.send("No games found", ephemeral=True)
            return

        embed = create_game_embed(games_data.get("games",None), title=f"Latest Games for {games_data.get('team',{}).get('name','N/A')} (Team ID: {games_data.get('team_id',None)})")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="upcoming", description="Get upcoming games")
    async def upcoming_games(self, interaction: discord.Interaction, team_id: int = None, limit: int = 5):
        await interaction.response.defer()

        
        games_data = await self.bot.api.get_upcoming_games(team_id=team_id, limit=limit)
        if not games_data:
            await interaction.followup.send("Team not found", ephemeral=True)
            return
        embed = create_game_embed(games_data.get("games",None), title=f"Upcoming games for {games_data.get('team',{}).get('name','N/A')} (Team ID: {games_data.get('team_id',None)})")
        await interaction.followup.send(embed=embed) 


async def setup(bot):
    await bot.add_cog(Games(bot))