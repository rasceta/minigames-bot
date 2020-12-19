import datetime
import discord
import util
import asyncio

from discord.ext import commands, tasks

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(name="send", description="Send message to a channel using bot", usage="send #channel [message]")
    async def send(self, ctx, channel:discord.TextChannel=None, *, msg:str=None):
        if ctx.author.guild_permissions.administrator:
            await ctx.message.delete()
            if channel is None or msg is None:
                return
            await channel.send(msg)

    @commands.guild_only()
    @commands.command('resetdaily')
    async def resetdaily(self, ctx):
        if ctx.author.guild_permissions.administrator:
            cursor = self.bot.conn.cursor()

            query = "UPDATE players SET next_daily_coins_time = current_timestamp"
            cursor.execute(query)
            self.bot.conn.commit()
            await ctx.message.add_reaction("✅")
            await ctx.send("All players free daily coins has been reset to now")

    @commands.guild_only()
    @commands.command('resetweekly')
    async def resetweekly(self, ctx):
        if ctx.author.guild_permissions.administrator:
            cursor = self.bot.conn.cursor()

            query = "UPDATE players SET next_weekly_coins_time = current_timestamp"
            cursor.execute(query)
            self.bot.conn.commit()
            await ctx.message.add_reaction("✅")
            await ctx.send("All players free weekly coins has been reset to now")

    @commands.has_permissions(administrator=True)
    @commands.command(name="setup", description="Setup minigames channels", usage="setup")
    async def setup(self, ctx):
        guild = ctx.guild

        cursor = self.bot.conn.cursor()

        query = "SELECT * FROM servers WHERE server_id = %s"
        cursor.execute(query, (guild.id,))
        result = cursor.fetchall()
        if not result:
            return

        new_category = await guild.create_category(name="Minigames")
        await new_category.set_permissions(guild.default_role, read_messages=True)
        count_game_channel = await new_category.create_text_channel(name="count-game")
        free_coins_channel = await new_category.create_text_channel(name="free-coins")
        query = "UPDATE servers SET count_game_channel_id = %s, free_coins_channel_id = %s WHERE server_id = %s"
        data = (count_game_channel.id, free_coins_channel.id, guild.id)
        cursor.execute(query, data)
        self.bot.conn.commit()

        query_insert = "INSERT INTO count_game(server_id, count_game_channel_id, last_count_member_id, last_count_number, last_count_status, last_count_fee, total_fee, created_at, last_modified_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        data_insert = (guild.id, count_game_channel.id, 1, 0, 'good', 300, 0, datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query_insert,data_insert)
        self.bot.conn.commit()

        embed = discord.Embed(title="Count Game", description="Let the count game begin! Starts from 1", color=discord.Color.teal())
        embed.set_thumbnail(url="https://i.imgur.com/DMvoEus.png")
        await count_game_channel.send(embed=embed)

        response = f"{count_game_channel.mention} and {free_coins_channel.mention} have been created!"
        response = util.log_embed(response, "success")
        await ctx.send(embed=response)

    @commands.has_permissions(administrator=True)
    @commands.command(name="purge", description="Purge channel messages", usage="purge")
    async def purge(self, ctx, limit:int=5):
        await ctx.channel.purge(limit=limit)

def setup(bot):
    bot.add_cog(Admin(bot))