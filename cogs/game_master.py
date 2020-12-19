import discord
import util

from discord.ext import commands

class Commisioner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.has_any_role("Game Master")
    @commands.command(name="startcount", description="Start a counting game on a channel", usage="startcount #channel")
    async def startcount(self, ctx, channel : discord.TextChannel=None):
        if channel is None:
            embed = util.log_embed("Please ping a channel you want to start counting game on", "failed")
            await ctx.send(embed=embed)
            return

        cursor = self.bot.conn.cursor()
        query = "UPDATE servers SET count_game_channel_id = %s WHERE server_id = %s"
        cursor.execute(query,(channel.id, ctx.guild.id))
        self.bot.conn.commit()
        try:
            query_insert = "INSERT INTO count_game(server_id, count_game_channel_id, last_count_member_id, last_count_number, last_count_status, last_count_fee, total_fee, created_at, last_modified_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            data_insert = (ctx.guild.id, channel.id, 1, 0, 'good', 300, 0, datetime.datetime.now(), datetime.datetime.now())
            cursor.execute(query_insert,data_insert)
        except:
            self.bot.conn.commit()
            query_update = "UPDATE count_game SET count_game_channel_id = %s, last_count_member_id = 1, last_count_number = %s, last_count_status = %s, last_count_fee = 300, total_fee = 0, last_modified_at = current_timestamp WHERE server_id = %s"
            data_update = (channel.id, 0, "good", ctx.guild.id)
            cursor.execute(query_update, data_update)
        self.bot.conn.commit()
        log_embed = util.log_embed(f"Successfully started counting game on {channel.mention}", "success")
        await ctx.send(embed=log_embed)
        embed = discord.Embed(title="Apollo's Chain Counting Game", description="Alright! Let's start all over again!", color=discord.Color.teal())
        embed.set_thumbnail(url="https://i.imgur.com/DMvoEus.png")
        await channel.send(embed=embed)

    @commands.guild_only()
    @commands.has_any_role("Game Master")
    @commands.command(name="resetcount", description="Reset counting game number and fee", usage="resetcount <number> <fee>")
    async def resetcount(self, ctx, count_number:int=None, fee:int=None):
        if count_number is None or fee is None:
            embed = util.log_embed("Please input the count number and fee", "failed")
            await ctx.send(embed=embed)
            return

        cursor = self.bot.conn.cursor()
        try:
            query = "UPDATE count_game SET last_count_member_id = 1, last_count_number = %s, last_count_fee = %s, last_count_status = %s WHERE server_id = %s"
            cursor.execute(query,(count_number, fee, "good", ctx.guild.id))
            self.bot.conn.commit()
            self.bot.logger.info("Updated channel count (reset_count)")
            response = f"Number and fee have been reset to {count_number} and {fee:,}"
            embed = util.log_embed(response, "success")
        except:
            response = f"You haven't set a count channel"
            embed = util.log_embed(response, "failed")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.has_any_role("Game Master")
    @commands.command(name="stopcount", description="Stop counting game (need to restart it with startcount command)", usage="stopcount")
    async def stopcount(self, ctx):
        cursor = self.bot.conn.cursor()
        query = "UPDATE servers SET count_game_channel_id = %s WHERE server_id = %s"
        cursor.execute(query,(1, ctx.guild.id))
        self.bot.conn.commit()
        try:
            query_update = "UPDATE count_game SET count_game_channel_id = %s WHERE server_id = %s"
            data_update = (1, ctx.guild.id)
            cursor.execute(query_update, data_update)
            self.bot.conn.commit()
            self.bot.logger.info("Updated channel count (stop_count)")
            response = f"Counting game has been stopped"
            embed = util.log_embed(response, "success")
        except:
            response = f"You haven't set a count channel"
            embed = util.log_embed(response, "failed")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.has_any_role("Game Master")
    @commands.command(name="addcoins", description="Add coins to a player", usage="addcoins @user <amount>")
    async def addcoins(self, ctx, member:discord.Member=None, coins:int=None):
        if member is None or coins is None:
            embed = util.log_embed("Please ping a player and input coins amount", "failed")
            await ctx.send(embed=embed)
            return

        cursor = self.bot.conn.cursor()
        query_add_coins = "UPDATE players SET coins = coins + %s, last_modified_at = current_timestamp where player_id = %s"
        data_add_coins = (coins, member.id)
        cursor.execute(query_add_coins, data_add_coins)
        self.bot.conn.commit()
        await ctx.message.add_reaction("✅")
        response = f"{ctx.author.mention} has added {coins:,} coins to {member.mention}"
        embed = util.log_embed(response, "success")
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Commisioner(bot))