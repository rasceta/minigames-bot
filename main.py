import discord
import os
import psycopg2
import util

from discord.ext import commands
from dotenv import load_dotenv
from bot import Minigames

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CONN = psycopg2.connect(user=os.getenv("DATABASE_USERNAME"),
                        password=os.getenv("DATABASE_PASSWORD"),
                        host=os.getenv("DATABASE_HOST"),
                        port=os.getenv("DATABASE_PORT"),
                        database=os.getenv("DATABASE_DB"))

client = Minigames("mini ", CONN)

@client.command()
async def load(ctx, extension):
    if ctx.author.id == 544155147572609024 or ctx.author.guild_permissions.administrator:
        client.load_extension(f"cogs.{extension}")
        embed = util.log_embed(f"{extension} module has been loaded!", "success")
        await ctx.send(embed=embed)

@client.command()
async def unload(ctx, extension):
    if ctx.author.id == 544155147572609024 or ctx.author.guild_permissions.administrator:
        client.unload_extension(f"cogs.{extension}")
        embed = util.log_embed(f"{extension} module has been unloaded!", "success")
        await ctx.send(embed=embed)

@client.command()
async def reload(ctx, extension):
    if ctx.author.id == 544155147572609024 or ctx.author.guild_permissions.administrator:
        client.unload_extension(f"cogs.{extension}")
        client.load_extension(f"cogs.{extension}")
        embed = util.log_embed(f"{extension} module has been reloaded!", "success")
        await ctx.send(embed=embed)

for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f"cogs.{filename[:-3]}")

client.run(TOKEN)