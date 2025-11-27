import discord
import datetime

def create_game_embed(games_data, title="Games List"):
    """
    Takes a list of games objects and returns a discord.Embed
    """

    if not games_data:
        return discord.Embed(title=title, description="No games found", color=discord.Color.red())
    
    embed = discord.Embed(title=title, color=discord.Color.green())


    for game in games_data:
        formatted_date = format_date(game.get('gameTime'))

        embed.add_field(
            name=f"{game.get('homeTeam', {}).get('name', 'Unknown')} vs {game.get('awayTeam', {}).get('name', 'Unknown')} | {game.get('location', 'Unknown')}",
            value=f"Score: {safe_get(game, 'homeScore', 0)} - {safe_get(game, 'awayScore', 0)} | {formatted_date}",
            inline=False
        )
    return embed

def format_date(date_str):
    """
    Takes date in form 'yyyy-mm-ddT%H:%M:%SZ' and returns a formatted string for Discord.
    """
    if date_str:
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            timestamp = int(dt.timestamp())
            formatted_date = f"<t:{timestamp}:f> (<t:{timestamp}:R>)"
            
        except ValueError:
            formatted_date = "Invalid Date"
    else:
        formatted_date = "TBD"

    return formatted_date

def safe_get(data, key, default="N/A"):
    """
    Safely gets a value. 
    If value is None, returns default. 
    If value is 0 (score), returns 0.
    """
    val = data.get(key)
    if val is None:
        return default
    return val