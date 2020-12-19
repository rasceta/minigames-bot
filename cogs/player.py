import util
import math
import random
import discord
import datetime
import asyncio

from discord.ext import commands
from helper import players_commands

TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

class Player(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.guild_only()
    @commands.command(
        name="wallet",
        aliases=["inv", "inventory"],
        description="Shows your inventory/wallet",
        usage="wallet"
    )
    async def wallet(self, ctx, member: discord.Member=None):

        role = discord.utils.find(lambda r: r.name == "Game Master", ctx.author.roles)
        if role is None or member is None:
            member = ctx.author

        cursor = self.bot.conn.cursor()
        query_coin = "SELECT coins FROM players where player_id = %s"
        data_coin = (member.id,)
        cursor.execute(query_coin,data_coin)
        result = cursor.fetchall()
        player_coin = [e[0] for e in result]
        player_coin = player_coin[0]

        query_items = "SELECT item_name FROM items where player_id = %s"
        data_items = (member.id,)
        cursor.execute(query_items,data_items)
        result = cursor.fetchall()
        items_list = [e[0] for e in result]
        if items_list == []:
            items_list = ["No Items"]
            item_response = ', '.join(items_list)
        else:
            item_response = ""
            unique_items = list(set(items_list))
            for i in unique_items:
                item_response = item_response + f"{i} ({items_list.count(i)})\n"

        embed = discord.Embed(title=f"Inventory",
                                color=discord.Color.gold())
        embed.set_thumbnail(url="https://i.imgur.com/egt7kT0.png")
        embed.set_author(name=member.name, icon_url=member.avatar_url)
        embed.add_field(name="💰Coins💰", value=f"{player_coin:,}", inline=False)
        embed.add_field(name="🎒Items🎒", value=item_response, inline=False)

        await ctx.send(embed=embed)
        return

    @commands.guild_only()
    @commands.command(
        name="lastcount",
        aliases=["lc","lcount","lastc"],
        description="Show last count info of counting game",
        usage="lastcount"
    )
    async def lastcount(self, ctx):
        cursor = self.bot.conn.cursor()

        query_last_count = 'SELECT last_count_number, last_count_member_id, last_count_fee FROM count_game WHERE server_id = %s'
        cursor.execute(query_last_count, (ctx.guild.id, ))
        result = cursor.fetchall()
        last_count_number = result[0][0]
        last_count_member_id = result[0][1]
        last_count_fee = result[0][2]

        embed = discord.Embed(title="Apollo's Chain Counting Game", description="Last Count", color=discord.Color.purple())
        embed.set_thumbnail(url="https://i.imgur.com/DMvoEus.png")
        embed.add_field(name="Member",value=f"<@{last_count_member_id}>")
        embed.add_field(name="Number",value=str(last_count_number))
        embed.add_field(name="Fee",value=f"{last_count_fee:,}")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(
        name="daily",
        description="Claim your daily reward",
        usage="daily"
    )
    async def daily(self, ctx):
        member = ctx.author
        conn = self.bot.conn
        cursor = conn.cursor()
        query_daily = "SELECT next_daily_coins_time FROM players where player_id = %s"
        data_daily = (member.id,)
        cursor.execute(query_daily,data_daily)
        result = cursor.fetchall()
        next_daily_coins = [e[0] for e in result]
        next_daily_coins = next_daily_coins[0]

        if(next_daily_coins is None or datetime.datetime.now() > next_daily_coins):
            daily_coins = 1000
            query = "UPDATE players SET player_name = %s, coins = coins + %s, next_daily_coins_time = %s where player_id = %s"
            next_daily_coins = datetime.datetime.now() + datetime.timedelta(days=1)
            data = (member.name, daily_coins, next_daily_coins, member.id)
            cursor.execute(query, data)
            conn.commit()
            await ctx.message.add_reaction("✅")
            await ctx.send(f"{member.mention}, you have claimed your daily reward of {daily_coins:,} coins! Please check again tomorrow!")
        else:
            next_daily_coins = next_daily_coins - datetime.datetime.now()
            minutes = int((next_daily_coins.seconds % 3600) / 60)
            hours = int(next_daily_coins.seconds / 3600)
            seconds = int(next_daily_coins.seconds % 60)
            if hours == 0:
                time_message = f"{minutes} minutes and {seconds} seconds"
                if minutes == 0:
                    time_message = f"{seconds} seconds"
            else:
                time_message = f"{hours} hours and {minutes} minutes"
            await ctx.message.add_reaction("❌")
            await ctx.send(f"{ctx.author.mention}, you still have {time_message} before your next daily reward!")
        conn.commit()

    @commands.guild_only()
    @commands.command(
        name="weekly",
        description="Claim your weekly reward",
        usage="weekly"
    )
    async def weekly(self, ctx):
        member = ctx.author
        conn = self.bot.conn
        cursor = conn.cursor()
        query_weekly = "SELECT next_weekly_coins_time FROM players where player_id = %s"
        data_weekly = (member.id,)
        cursor.execute(query_weekly,data_weekly)
        result = cursor.fetchall()
        next_weekly_coins = [e[0] for e in result]
        next_weekly_coins = next_weekly_coins[0]

        if (next_weekly_coins is None or datetime.datetime.now() > next_weekly_coins):
            weekly_coins = 10000
            query = "UPDATE players SET player_name = %s, coins = coins + %s, next_weekly_coins_time = %s where player_id = %s"
            next_weekly_coins = datetime.datetime.now() + datetime.timedelta(weeks=1)
            data = (member.name, weekly_coins, next_weekly_coins, member.id)
            cursor.execute(query, data)
            conn.commit()
            await ctx.message.add_reaction("✅")
            await ctx.send(f"You have claimed your {weekly_coins:,} weekly coins, {member.mention}. Don't forget next week!")
        else:
            next_weekly_coins = next_weekly_coins - datetime.datetime.now()
            days = int(next_weekly_coins.days)
            minutes = int((next_weekly_coins.seconds % 3600) / 60)
            hours = int(next_weekly_coins.seconds / 3600)
            seconds = int(next_weekly_coins.seconds % 60)
            if days == 0:
                time_message = f"{hours} hours and {minutes} minutes"
                if hours == 0:
                    time_message = f"{minutes} minutes and {seconds} seconds"
                    if minutes == 0:
                        time_message = f"{seconds} seconds"
            else:
                time_message = f"{days} days and {hours} hours"
            await ctx.message.add_reaction("❌")
            await ctx.send(f"{ctx.author.mention}, you still have {time_message} before your next weekly reward!")
        conn.commit()

    @commands.guild_only()
    @commands.command(
        name="donate",
        description="Donate some coins to other player",
        usage="donate @user <coins amount>"
    )
    async def donate(self, ctx, member:discord.Member=None, donation_amount:int=None):
        donater = ctx.author
        if member is None or donation_amount is None:
            response = f"Sorry, you need to ping the recipient and type the donation amount"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        if donation_amount < 0:
            await ctx.message.add_reaction("❌")
            response = f"Sorry, {ctx.author.mention}. Please input correct amount of coins"

        cursor = self.bot.conn.cursor()

        query = "SELECT coins FROM players WHERE player_id = %s"
        data = (donater.id,)
        cursor.execute(query,data)
        result = cursor.fetchall()
        player_coin  = [e[0] for e in result]
        player_coin = player_coin[0]

        query = "SELECT next_donation_time FROM players WHERE player_id = %s"
        data = (member.id,)
        cursor.execute(query,data)
        result = cursor.fetchall()

        if donation_amount > player_coin:
            await ctx.message.add_reaction("❌")
            response = f"Sorry {donater.mention}. Looks like you don't have that much coins"
            return response

        query_donater = "UPDATE players SET coins = coins - %s, last_modified_at = %s where player_id = %s"
        data_donater = (donation_amount, datetime.datetime.now(), donater.id)
        cursor.execute(query_donater, data_donater)
        query_donate_to = "UPDATE players SET coins = coins + %s, last_modified_at = %s where player_id = %s"
        data_donate_to = (donation_amount, datetime.datetime.now(), member.id)
        cursor.execute(query_donate_to, data_donate_to)
        self.bot.conn.commit()
        await ctx.message.add_reaction("✅")
        response = f"{donater.mention} successfully donated {donation_amount:,} coins to {member.mention}"
        await ctx.send(response)

    @commands.guild_only()
    @commands.command(
        name="shop",
        description="Shows shop",
        usage="shop"
    )
    async def shop(self, ctx, page:int=1):
        items = util.read_json('items.json')
        items_shop = items['shop']
        embed = discord.Embed(
            title="Apollo's Shop",
            description=f"Welcome to Apollo's Shop!\nYou can purchase any of these items by typing `{ctx.prefix}purchase <itemcode>`",
            color=discord.Color.green()
        )

        pagesize = 7
        start = (page - 1) * pagesize
        end = (page * pagesize)
        total_page = math.ceil(len(items_shop) / pagesize)

        for i in items_shop[start:end]:
            embed.add_field(name=f"{i['item_description']}",value=f"Price: {i['item_price']:,} - `itemcode: {i['item_code']}`", inline=False)
        if total_page > 1:
            embed.set_footer(text=f"Page {page}/{total_page}. Type {ctx.prefix}shop <number> to show another page")

        embed.add_field(name="Notes",value=f"If you want to turn in your items, Please exchange with this format\n`{ctx.prefix}exchange <item code> <quantity> <dodo code>`\n**Please be sure to open your island before turning in a token!**",inline=False)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(name="purchase", aliases=["buy"], description="Purchase items from shop", usage="purchase <itemcode> <quantity>")
    async def purchase(self, ctx, itemcode:str=None, quantity:int=1):
        if itemcode is None:
            response = f"Sorry {ctx.author.mention}. You need to type an item code"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        conn = self.bot.conn
        member = ctx.author
        itemcode = itemcode.lower()

        ITEMS = util.read_json('items.json')
        ITEMS_SHOP = ITEMS['shop']
        ITEM_CODE = [row['item_code'] for row in ITEMS_SHOP]

        shop_roles = {
            "role_1": 12313231323, # role id example
        }
        if itemcode not in ITEM_CODE and itemcode not in shop_roles:
            await ctx.message.add_reaction("❌")
            response = f"Item code not found. Please try again"
            return response

        item_dict = next(e for e in ITEMS_SHOP if e["item_code"] == itemcode)
        item_price = item_dict["item_price"]
        item_name = item_dict["item_name"]
        item_code = item_dict["item_code"]

        cursor = conn.cursor()
        query_coin = "SELECT coins FROM players WHERE player_id = %s"
        data_coin = (member.id,)
        cursor.execute(query_coin,data_coin)
        result = cursor.fetchall()
        result_list = result[0]
        player_coin = result_list[0]

        if player_coin < item_price * quantity:
            response = f"Sorry {member.mention}. You don't seem to have that much coins to purchase this item"
            embed = util.log_embed(response, "failed")
            await ctx.send(embed=embed)
            return

        has_role = False
        if itemcode not in shop_roles:
            for _ in range(0, quantity):
                query_item = "INSERT INTO items (player_id,item_name,item_code,created_at,last_modified_at) VALUES (%s,%s,%s,%s,%s)"
                data_item = (member.id, item_name, item_code, datetime.datetime.now(), datetime.datetime.now())
                query_coin = "UPDATE players SET coins = coins - %s, last_modified_at = %s WHERE player_id = %s"
                data_coin = (item_price, datetime.datetime.now(), member.id)
                cursor.execute(query_item,data_item)
                conn.commit()
                cursor.execute(query_coin, data_coin)
                conn.commit()
        elif itemcode in shop_roles:
            if discord.utils.get(member.roles, id=shop_roles[itemcode]) is not None:
                has_role = True
            else:
                query_coin = "UPDATE players SET coins = coins - %s, last_modified_at = %s WHERE player_id = %s"
                data_coin = (item_price, datetime.datetime.now(), member.id)
                cursor.execute(query_coin, data_coin)
                conn.commit()
                await member.add_roles(discord.utils.get(member.guild.roles, id=shop_roles[itemcode]))

        if has_role is False:
            response = f"{member.mention} has purchased `{item_name}`!"
            response = util.log_embed(response, "success")
        else:
            response = f"{member.mention}, you already have the role!"
            response = util.log_embed(response, "failed")

        await ctx.send(embed=response)

    @commands.guild_only()
    @commands.command(name="leaderboard", aliases=["rank"], description="Shows leaderboard", usage="leaderboard")
    async def leaderboard(self, ctx, number=10):
        cursor = self.bot.conn.cursor()

        query_guess_time = "SELECT max_card_games_reaction_time FROM servers WHERE server_id = %s"
        cursor.execute(query_guess_time, (ctx.guild.id,))
        result = cursor.fetchall()
        max_card_games_reaction_time = result[0]
        max_card_games_reaction_time = max_card_games_reaction_time[0]
        if max_card_games_reaction_time is None:
            max_card_games_reaction_time = datetime.datetime.now()
        if datetime.datetime.now() < max_card_games_reaction_time:
            response = "Leaderboard is disabled until card game is finished"
            await ctx.send(response)
            return

        cursor = self.bot.conn.cursor()
        query_rank = "SELECT player_name, coins FROM players ORDER BY coins DESC"
        cursor.execute(query_rank)
        result = cursor.fetchall()
        player_name = [e[0] for e in result]
        player_coins = [e[1] for e in result]

        response = ""
        if len(player_coins) < 10:
            for i in range(0,len(player_coins)):
                response = response + f"#**{i+1}** Name : **{player_name[i]}** | Coins : **{player_coins[i]:,}**\n"
        else:
            for i in range(0,10):
                response = response + f"#**{i+1}** Name : **{player_name[i]}** | Coins : **{player_coins[i]:,}**\n"

        embed = discord.Embed(title="**Apollo Games Leaderboard**", 
                            color=discord.Color.gold(),
                            description=response)
        embed.set_thumbnail(url="https://i.imgur.com/GzSL5XY.png")

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Player(bot))