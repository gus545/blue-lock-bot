import discord
import os
import aiohttp
from discord.ext import commands
from dotenv import load_dotenv
from services.api import LeagueClient


load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://localhost:8000")

intents = discord.Intents.default()
intents.message_content = True 

class LeagueBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.session: aiohttp.ClientSession = None
        self.api: LeagueClient = None

    async def setup_hook(self):
        print("--- Starting Bot Setup ---")
        self.session = aiohttp.ClientSession()
        
        self.api = LeagueClient(self.session, API_URL)
        print("--- API Initialized ---")


        # Load Cogs
        initial_extensions = ['cogs.games']
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded extension: {extension}")
            except Exception as e:
                print(f"Failed to load extension {extension}: {e}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def close(self):
        await self.session.close()
        await super().close()

bot = LeagueBot()

@bot.command(name="sync")
@commands.is_owner()
async def sync_commands(ctx):
    if ctx.guild:
        # Sync to the current server
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Synced {len(synced)} commands to this server!")
    else:
        # Sync globally
        synced = await bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands globally!")

if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)