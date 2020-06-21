import discord
import psycopg2
import json
import random
import os
import asyncio
import datetime

from discord.ext import commands, tasks
from dotenv import load_dotenv

from queries import create_tables
from guide_string import get_guide_string
from custom_functions.slotmachine import get_slot
from custom_functions.cardgames import get_card_game_intro, get_random_card_game_name, get_card_game_outro

client = commands.Bot(('!apollo ','!Apollo ','!a ','!A '))
BOT_PREFIX = client.command_prefix
load_dotenv()
TOKEN = os.getenv("APOLLO_TOKEN")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

async def get_conn():
    conn = psycopg2.connect(user=os.getenv("DATABASE_USERNAME"),
                            password=os.getenv("DATABASE_PASSWORD"),
                            host=os.getenv("DATABASE_HOST"),
                            port=os.getenv("DATABASE_PORT"),
                            database=os.getenv("DATABASE_DB"))
    return conn

@tasks.loop(minutes=5)
async def apollo_free_coins():
    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT free_coins_channel_id from servers"
    cursor.execute(query)
    result = cursor.fetchall()
    free_coins_channel_id_list = [e[0] for e in result]

    channel_id = 0
    for channel_id in free_coins_channel_id_list:
        if channel_id != None:
            channel = client.get_channel(channel_id)
            embed = discord.Embed(title="Free Coins",
                                description=f"Hello, hello! The mysterious coin creature's here. It has returned for all to see! It's here to give you all free coins! Yes! You heard that right! Free coins!")
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png")
            embed.set_footer(text="React with the 👍 reaction! Quickly! I must go in 40 seconds!")
            new_message = await channel.send(embed=embed)
            await new_message.add_reaction("👍")
            max_reaction_time = datetime.datetime.now() + datetime.timedelta(seconds=40)

            query = "UPDATE servers SET last_free_coins_message_id = %s, max_free_coins_reaction_time = %s WHERE free_coins_channel_id = %s"
            data = (new_message.id, max_reaction_time, channel_id)
            cursor.execute(query,data)
            conn.commit()
            conn.close()

    embed = discord.Embed(title="Free Coins",
                        description="I must go now! Toodle doo~ I'll be back whenever!")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png")
    embed.set_footer(text="In the meantime! Please check out #community features!")
    await asyncio.sleep(40)
    for channel_id in free_coins_channel_id_list:
        if channel_id != None:
            channel = client.get_channel(channel_id)
            await channel.send(embed=embed)

@apollo_free_coins.before_loop
async def apollo_free_coins_before():
    await client.wait_until_ready()

@tasks.loop(minutes=3)
async def apollo_card_games():
    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT card_game_channel_id from servers"
    cursor.execute(query)
    result = cursor.fetchall()
    card_game_channel_id_list = [e[0] for e in result]

    game_name = get_random_card_game_name()
    game_intro = get_card_game_intro(game_name)
    choices = []
    if game_name == "GTC":
        choices = ["black","red"]
    elif game_name == "PCC":
        choices = ["spade","club","diamond","heart"]
    elif game_name == "ACE":
        choices = range(1,11)
    answer = random.choice(choices)

    embed = discord.Embed(title=game_intro[0],description=game_intro[1],color=discord.Color.red())
    embed.set_image(url=game_intro[2])
    embed.set_thumbnail(url="http://clipart-library.com/images/pT5o6baac.jpg")

    for channel_id in card_game_channel_id_list:
        if channel_id != None:
            channel = client.get_channel(channel_id)
            new_message = await channel.send(embed=embed)
            max_card_games_reaction_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

            query = "UPDATE servers SET last_card_games_name = %s, last_card_games_answer = %s, last_card_games_message_id = %s, max_card_games_reaction_time = %s, last_modified_at = %s WHERE card_game_channel_id = %s"
            data = (game_name, answer, new_message.id, max_card_games_reaction_time, datetime.datetime.now(), channel_id)
            cursor.execute(query,data)
            conn.commit()

    try:
        await asyncio.sleep(60)
        query_rank = "SELECT player_name, last_card_game_answer, last_card_game_bet FROM players WHERE last_card_game_answer_time + INTERVAL '1 m' >= NOW()"
        cursor.execute(query_rank)
        result = cursor.fetchall()
        player_name = [e[0] for e in result]
        player_answers = [e[1] for e in result]
        player_bets = [e[2] for e in result]

        print(f"Game Name : {game_name}, Player Name : {player_name}, Player answer : {player_answers}, Player Bets : {player_bets}")

        players_won = "No Winners"
        for i, val in enumerate(player_answers):
            if isinstance(answer, int):
                val = int(val)
            if val == answer:
                if players_won == "No Winners":
                    players_won = ""
                players_won = players_won + f"\n**{player_name[i]}** won **{player_bets[i]*2}**"

        game_outro = get_card_game_outro(game_name,answer)
        embed = discord.Embed(title=game_outro[0],description=game_outro[1],color=discord.Color.blue())
        embed.set_image(url=game_outro[2])
        embed.set_thumbnail(url="http://clipart-library.com/images/pT5o6baac.jpg")
        embed.add_field(name="**Winners**",value=players_won)

        for c_id in card_game_channel_id_list:
            if c_id != None:
                channel = client.get_channel(c_id)    
                await channel.send(embed=embed)
        
        conn.close()
    except Exception as e:
        print(e)

@apollo_card_games.before_loop
async def apollo_card_games_before():
    await client.wait_until_ready()

@client.event
async def on_ready():
    await create_tables()
    print(f'Apollo Bot is Ready')
    await client.change_presence(activity=discord.Game('Apollo Games'))

@client.event
async def on_guild_join(guild):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "INSERT INTO servers(server_id,server_name,created_at,last_modified_at) VALUES(%s,%s,%s,%s)"
    data = (guild.id, guild.name, datetime.datetime.now(), datetime.datetime.now())
    cursor.execute(query,data)
    conn.commit()
    conn.close()

@client.event
async def on_raw_reaction_add(payload):
    user_id = payload.user_id
    message_id = payload.message_id
    guild_id = payload.guild_id

    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT last_free_coins_message_id, max_free_coins_reaction_time from servers WHERE server_id = %s"
    data = (guild_id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    last_message_id = result[0][0]
    max_reaction_time = result[0][1]
    try:
        if (message_id == last_message_id) and (user_id != 721001236589183070):
            time_now = datetime.datetime.now()
            if time_now <= max_reaction_time:
                if payload.emoji.name == '👍':
                    query = "UPDATE players SET coins = coins + %s WHERE player_id = %s"
                    data = (200,user_id)
                    cursor.execute(query,data)
                    conn.commit()
                    conn.close()
            else:
                pass
    except:
        print('Max free coins reaction time is not set')

@client.event
async def on_raw_reaction_remove(payload):
    user_id = payload.user_id
    message_id = payload.message_id
    guild_id = payload.guild_id

    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT last_free_coins_message_id, max_free_coins_reaction_time from servers WHERE server_id = %s"
    data = (guild_id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    last_message_id = result[0][0]
    max_reaction_time = result[0][1]
    try:
        if message_id == last_message_id:
            time_now = datetime.datetime.now()
            if time_now <= max_reaction_time:
                if payload.emoji.name == '👍':
                    query = "UPDATE players SET coins = coins - %s WHERE player_id = %s"
                    data = (200,user_id)
                    cursor.execute(query,data)
                    conn.commit()
                    conn.close()
            else:
                pass
    except:
        print('Max free coins reaction time is not set')

@client.event
async def on_message(message):
    try:
        conn = await get_conn()
        cursor = conn.cursor()
        query = "INSERT INTO servers(server_id,server_name,created_at,last_modified_at) VALUES(%s,%s,%s,%s)"
        data = (message.guild.id, message.guild.name, datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query,data)
        conn.commit()
        conn.close()
    except:
        pass
    await client.process_commands(message)

@commands.has_permissions(administrator=True)
@client.command()
async def clear(ctx, limits=5):
    await ctx.channel.purge(limit=limits)

@commands.has_permissions(administrator=True)
@client.command('free_coins_channel')
async def free_coins_channel(ctx, channel: discord.TextChannel):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET free_coins_channel_id = %s WHERE server_id = %s"
    data = (channel.id, ctx.guild.id)
    cursor.execute(query, data)
    conn.commit()
    conn.close()

    await ctx.message.add_reaction("✅")
    await ctx.send(f"You have set {channel.mention} as `Free Coins Channel`")

@free_coins_channel.error
async def free_coins_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        conn = await get_conn()
        cursor = conn.cursor()
        query = "UPDATE servers SET free_coins_channel_id = %s WHERE server_id = %s"
        data = (ctx.channel.id, ctx.guild.id)
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        
        await ctx.message.add_reaction("✅")
        await ctx.send("You have set this channel as `Free Coins Channel`")

@commands.has_permissions(administrator=True)
@client.command('card_game_channel')
async def card_game_channel(ctx, channel: discord.TextChannel):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET card_game_channel_id = %s WHERE server_id = %s"
    data = (channel.id, ctx.guild.id)
    cursor.execute(query, data)
    conn.commit()
    conn.close()

    await ctx.message.add_reaction("✅")
    await ctx.send(f"You have set {channel.mention} as `Card Game Channel`")

@card_game_channel.error
async def card_game_channel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        conn = await get_conn()
        cursor = conn.cursor()
        query = "UPDATE servers SET card_game_channel_id = %s WHERE server_id = %s"
        data = (ctx.channel.id, ctx.guild.id)
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        
        await ctx.message.add_reaction("✅")
        await ctx.send("You have set this channel as `Card Game Channel`")

@commands.has_permissions(administrator=True)
@client.command('exchange_channel')
async def exchange_channel(ctx, channel : discord.TextChannel):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET exchange_channel_id = %s WHERE server_id = %s"
    data = (channel.id, ctx.guild.id)
    cursor.execute(query, data)
    conn.commit()
    conn.close()
    
    await ctx.message.add_reaction("✅")
    await ctx.send(f"You have set {channel.mention} as `Exchange Channel`")

@exchange_channel.error
async def exchange_channel_error(ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
        conn = await get_conn()
        cursor = conn.cursor()
        query = "UPDATE servers SET exchange_channel_id = %s WHERE server_id = %s"
        data = (ctx.channel.id, ctx.guild.id)
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        
        await ctx.message.add_reaction("✅")
        await ctx.send("You have set this channel as `Exchange Channel`")


@commands.has_permissions(administrator=True)
@client.command('slot_game_channel')
async def slot_game_channel(ctx, channel : discord.TextChannel):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET slot_game_channel_id = %s WHERE server_id = %s"
    data = (channel.id, ctx.guild.id)
    cursor.execute(query, data)
    conn.commit()
    conn.close()
    
    await ctx.message.add_reaction("✅")
    await ctx.send(f"You have set {channel.mention} as `Slot machine game Channel`")

@slot_game_channel.error
async def slot_game_channel_error(ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
        conn = await get_conn()
        cursor = conn.cursor()
        query = "UPDATE servers SET slot_game_channel_id = %s WHERE server_id = %s"
        data = (ctx.channel.id, ctx.guild.id)
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        
        await ctx.message.add_reaction("✅")
        await ctx.send("You have set this channel as `Slot game Channel`")

@commands.has_permissions(administrator=True)
@client.command('count_game_channel')
async def count_game_channel(ctx, channel : discord.TextChannel):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET count_game_channel_id = %s WHERE server_id = %s"
    data = (channel.id, ctx.guild.id)
    cursor.execute(query, data)
    conn.commit()
    conn.close()
    
    await ctx.message.add_reaction("✅")
    await ctx.send(f"You have set {channel.mention} as `Chain counting game Channel`")

@count_game_channel.error
async def count_game_channel_error(ctx,error):
    if isinstance(error, commands.MissingRequiredArgument):
        conn = await get_conn()
        cursor = conn.cursor()
        query = "UPDATE servers SET count_game_channel_id = %s WHERE server_id = %s"
        data = (ctx.channel.id, ctx.guild.id)
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        
        await ctx.message.add_reaction("✅")
        await ctx.send("You have set this channel as `Chain counting game Channel`")

@commands.has_permissions(administrator=True)
@client.command('query')
async def query(ctx, *, query : str):
    if 'select' in query.lower():
        user = client.get_user(ctx.author.id)
        conn = await get_conn()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        await user.send(result)

@commands.has_permissions(administrator=True)
@client.command('start')
async def start(ctx, *, task_name: str):
    if task_name == "card":
        apollo_card_games.start()
    elif task_name == "coins":
        apollo_free_coins.start()
    await ctx.message.add_reaction("✅")
    await ctx.author.send(f"{task_name} has successfully started.")

@commands.has_permissions(administrator=True)
@client.command('stop')
async def stop(ctx, *, task_name: str):
    if task_name == "card":
        apollo_card_games.stop()
    elif task_name == "coins":
        apollo_free_coins.stop()
    await ctx.message.add_reaction("✅")
    await ctx.author.send(f"{task_name} has successfully stopped.")

@commands.has_role('Game Master')
@client.command('add_coins')
async def add_coins(ctx, member : discord.User, coins : int):
    conn = await get_conn()
    cursor = conn.cursor()
    query_add_coins = "UPDATE players SET coins = coins + %s, last_modified_at = current_timestamp where player_id = %s"
    data_add_coins = (coins, member.id)
    cursor.execute(query_add_coins, data_add_coins)
    conn.commit()
    conn.close()
    await ctx.message.add_reaction("✅")
    await ctx.send(f"Successfully added {coins} coins to {member.mention}")

@add_coins.error
async def add_coins_eror(ctx,error):
    if isinstance(error, commands.MissingRole):
        await ctx.send(error)
    else:
        await ctx.send(f"```Sorry, You need to define @Member you want to add their coins and the coin amount. Example of proper usage:\n\n!apollo add_coins @Member 1000```")

@client.command('register')
async def register(ctx):
    player = ctx.author
    conn = await get_conn()
    cursor = conn.cursor()
    try:
        query = '''INSERT INTO players (player_id, player_name, register_date, coins, next_slot_time, next_donate_time, 
        next_donation_time, next_daily_coins_time, created_at, last_modified_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
        next_donate_time = datetime.datetime.now() + datetime.timedelta(minutes=60)
        next_donation_time = datetime.datetime.now() + datetime.timedelta(minutes=60)
        next_slot_time = datetime.datetime.now()
        data = (player.id, player.name, datetime.datetime.now(), 1000, next_slot_time, next_donate_time, next_donation_time,
        datetime.datetime.now(), datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query,data)
        conn.commit()
        conn.close()
        await ctx.send(f"{player.mention} just registered into the game!")
        await ctx.message.add_reaction("✅")
    except:
        await ctx.send(f"Uh Oh! Looks like You're already registered")

@client.command(name='slot',aliases=['slots'])
async def slot(ctx, bet_amount : int):
    member = ctx.author
    slot = get_slot()
    stars_count = slot.count('⭐')

    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT next_slot_time, coins FROM players where player_id = %s"
    data = (member.id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    next_slot_time = [e[0] for e in result]
    player_coin = [e[1] for e in result]
    next_slot_time = next_slot_time[0]
    player_coin = player_coin[0]

    query = "SELECT slot_game_channel_id from servers"
    cursor.execute(query)
    result = cursor.fetchall()
    result_list = [e[0] for e in result]

    if ctx.channel.id in result_list:
        if bet_amount <= 2000:
            if bet_amount <= player_coin:
                if (next_slot_time == None) or (datetime.datetime.now() > next_slot_time):
                    if stars_count == 1:
                        response = f"Oh, that's too bad! Poor <@{member.id}> landed 1 star. Here you go! **{int(bet_amount*0.4)}** coins for you!"
                        coins = int(bet_amount*0.4) - bet_amount
                    elif stars_count == 2:
                        response = f"Hey, not bad! <@{member.id}> rolled 2 stars! Take it! **{int(bet_amount*(1.3))}** coins for you!"
                        coins = int(bet_amount*(1.3)) - bet_amount
                    elif stars_count == 3:
                        response = f"Congratulations! <@{member.id}> rolled 3 stars! Amazing! **{int(bet_amount*2)}** coins for you!"
                        coins = int(bet_amount*2) - bet_amount
                    elif stars_count == 4:
                        response = f"Sensational! <@{member.id}> rolled 4 stars! What are the odds? You deserve it! **{int(bet_amount*4)}** coins for you!"
                        coins = int(bet_amount*4) - bet_amount
                    else:
                        response = f"Hey, there's always next time <@{member.id}>. Feel free to try again!"
                        coins = -bet_amount
                    
                    query = "UPDATE players SET coins = coins + %s, next_slot_time = %s, last_modified_at = %s WHERE player_id = %s"
                    next_slot_time = datetime.datetime.now() + datetime.timedelta(seconds=10)
                    data = (coins,next_slot_time, datetime.datetime.now(), member.id)
                    cursor.execute(query,data)
                    conn.commit()
                    conn.close()
                    embed = discord.Embed(title="** Apollo's Slot Machine**",
                                        description="Place a bet and slot!"  )
                    embed.set_thumbnail(url="https://img.freepik.com/free-vector/slot-machine-colorful-neon-sign-machine-shape-with-triple-seven-brick-wall-background_1262-11913.jpg?size=338&ext=jpg")
                    embed.add_field(name=' | '.join(slot), value=response)
                    await ctx.message.add_reaction("✅")
                    await ctx.send(embed=embed)
                else:
                    next_slot_time = next_slot_time - datetime.datetime.now()
                    minutes = int((next_slot_time.seconds % 3600) / 60)
                    seconds = int(next_slot_time.seconds % 60)
                    await ctx.message.add_reaction("❌")
                    await ctx.send(f"Uh Oh! <@{member.id}> can use slot machine again in {minutes}m and {seconds}s")
            else:
                await ctx.message.add_reaction("❌")
                await ctx.send(f"Uh Oh! <@{member.id}> doesn't seem have enough coins to bet.")
        else:
            await ctx.message.add_reaction("❌")
            await ctx.send(f"Uh Oh! <@{member.id}>'s bet amount must be below 2000.")
    else:
        await ctx.message.add_reaction("❌")
        await ctx.send(f"Uh Oh! <@{member.id}> can only play slot in slot machine channel.")

@slot.error
async def slot_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
    else:
        await ctx.send("```Uh Oh! You can use slot machine and place a bet up to 2000 coins. Example of proper usage:\n\n!apollo slot 100```")

@commands.has_permissions(administrator=True)
@client.command('send')
async def send(ctx, channel : discord.TextChannel, *, message):
    await channel.send(message)

@commands.has_role('Game Master')
@client.command(name='items',aliases=['wallet','inventory','inv'])
async def items(ctx, member: discord.User):

    conn = await get_conn()
    cursor = conn.cursor()
    query_coin = "SELECT coins FROM players where player_id = %s"
    data_coin = (member.id,)
    cursor.execute(query_coin,data_coin)
    result = cursor.fetchall()
    player_coin = [e[0] for e in result]
    player_coin = player_coin[0]

    try:
        query_items = "SELECT item_name FROM items where player_id = %s"
        data_items = (member.id,)
        cursor.execute(query_items,data_items)
        result = cursor.fetchall()
        items_list = [e[0] for e in result]
        if items_list == []:
            items_list = ["No Items"]
    except:
        pass
    conn.close()

    embed = discord.Embed(title=f"{member.name}'s items info",
                            color=discord.Color.gold())
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png")
    embed.add_field(name="Name", value=member.name, inline=False)
    embed.add_field(name="💰Coins", value=player_coin, inline=False)
    embed.add_field(name="🎒Items", value=", ".join(items_list), inline=False)
    await ctx.send(embed=embed)

@items.error
async def items_error(ctx,error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
        await ctx.send(error)
    elif isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingRequiredArgument):
        member = ctx.author
        conn = await get_conn()
        cursor = conn.cursor()
        query_coin = "SELECT coins, last_card_game_answer_time FROM players where player_id = %s"
        data_coin = (member.id,)
        cursor.execute(query_coin,data_coin)
        result = cursor.fetchall()
        player_coin = [e[0] for e in result]
        player_answer_time = [e[1] for e in result]
        player_coin = player_coin[0]
        player_answer_time = player_answer_time[0]

        if (player_answer_time == None) or (datetime.datetime.now() > player_answer_time + datetime.timedelta(minutes=1)):
            items_list = ["No Items"]
            try:
                query_items = "SELECT item_name FROM items where player_id = %s"
                data_items = (member.id,)
                cursor.execute(query_items,data_items)
                result = cursor.fetchall()
                items_list = [e[0] for e in result]
                if items_list == []:
                    items_list = ["No Items"]
            except:
                pass
            conn.close()

            embed = discord.Embed(  title=f"{member.name}'s items info",
                                    color=discord.Color.gold())
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png")
            embed.add_field(name="Name", value=member.name, inline=False)
            embed.add_field(name="💰Coins", value=player_coin, inline=False)
            embed.add_field(name="🎒Items", value=", ".join(items_list), inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Uh Oh! {member.mention} you can check your wallet 1 minute after locking in an answer!")

@client.command('daily')
async def daily(ctx):
    member = ctx.author
    conn = await get_conn()
    cursor = conn.cursor()
    query_daily = "SELECT next_daily_coins_time FROM players where player_id = %s"
    data_daily = (member.id,)
    cursor.execute(query_daily,data_daily)
    result = cursor.fetchall()
    next_daily_coins = [e[0] for e in result]
    next_daily_coins = next_daily_coins[0]

    if isinstance(next_daily_coins, datetime.datetime):
        if (datetime.datetime.now () > next_daily_coins):
            if discord.utils.get(member.roles, name="💎Giver💎") is not None:
                free_coins = 10000
            elif discord.utils.get(member.roles, name="🔰 Donor 🔰") is not None:
                free_coins = 1500
            elif discord.utils.get(member.roles, name="Members") is not None:
                free_coins = 400
            query = "UPDATE players SET coins = coins + %s, next_daily_coins_time = %s where player_id = %s"
            next_daily_coins = datetime.datetime.now() + datetime.timedelta(days=1)
            data = (free_coins, next_daily_coins, member.id)
            cursor.execute(query, data)
            await ctx.message.add_reaction("✅")
            await ctx.send(f"{ctx.author.mention}, thank you! You have claimed your daily reward of {free_coins} coins! Please check again tomorrow!")
        else:
            next_daily_coins = next_daily_coins - datetime.datetime.now()
            minutes = int((next_daily_coins.seconds % 3600) / 60)
            hours = int(next_daily_coins.seconds / 3600)
            seconds = int(next_daily_coins.seconds % 60)
            await ctx.message.add_reaction("❌")
            await ctx.send(f"{ctx.author.mention}, you still have {hours} hour(s) {minutes} minute(s) and {seconds} second(s) before your next daily reward!")
    conn.commit()
    conn.close()

@daily.error
async def daily_error(ctx,error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.message.add_reaction("❌")
        await ctx.send(f"{ctx.author.mention} you can't claim your daily rewards because you have not registered! Please type `!apollo register`")

@commands.has_permissions(administrator=True)
@client.command('reset_daily')
async def reset_daily(ctx):
    conn = await get_conn()
    cursor = conn.cursor()

    query = "UPDATE players SET next_daily_coins_time = current_timestamp"
    cursor.execute(query)
    conn.commit()
    conn.close()
    await ctx.message.add_reaction("✅")
    await ctx.send("All players free daily coins has been reset to now")

@client.command('donate')
async def donate(ctx, member : discord.User, donation_amount : int):
    donater = ctx.author

    conn = await get_conn()
    cursor = conn.cursor()

    query = "SELECT next_donate_time,coins FROM players WHERE player_id = %s"
    data = (donater.id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    donate_time = [e[0] for e in result]
    player_coin  = [e[1] for e in result]
    next_donate_time = donate_time[0]
    player_coin = player_coin[0]

    query = "SELECT next_donation_time FROM players WHERE player_id = %s"
    data = (member.id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    donation_time = [e[0] for e in result]
    next_donation_time = donation_time[0]

    if donation_amount <= player_coin:
        if (donation_amount <= 50000):
            if (datetime.datetime.now() > next_donate_time):
                if (datetime.datetime.now() > next_donation_time):
                    query_donater = "UPDATE players SET coins = coins - %s, next_donate_time = %s, last_modified_at = %s where player_id = %s"
                    next_donate_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
                    data_donater = (donation_amount, next_donate_time, datetime.datetime.now(), donater.id)
                    cursor.execute(query_donater, data_donater)
                    query_donate_to = "UPDATE players SET coins = coins + %s, next_donation_time = %s, last_modified_at = %s where player_id = %s"
                    next_donation_time = datetime.datetime.now() + datetime.timedelta(minutes=1)
                    data_donate_to = (donation_amount, next_donation_time, datetime.datetime.now(), member.id)
                    cursor.execute(query_donate_to, data_donate_to)
                    conn.commit()
                    await ctx.message.add_reaction("✅")
                    response = f"<@{donater.id}> Successfully donated {donation_amount} coins to <@{member.id}>"
                else:
                    next_donation_time = next_donation_time - datetime.datetime.now()
                    minutes = int((next_donation_time.seconds % 3600) / 60)
                    hours = int(next_donation_time.seconds / 3600)
                    seconds = int(next_donation_time.seconds % 60)
                    await ctx.message.add_reaction("❌")
                    response = f"Donation failed. <@{member.id}> will be able to be donated in {hours} hour(s) {minutes} minute(s) and {seconds} second(s)"
            else:
                next_donate_time = next_donate_time - datetime.datetime.now()
                minutes = int((next_donate_time.seconds % 3600) / 60)
                hours = int(next_donate_time.seconds / 3600)
                seconds = int(next_donate_time.seconds % 60)
                await ctx.message.add_reaction("❌")
                response = f"Donation failed. <@{donater.id}> will be able to donate in {hours} hour(s) {minutes} minute(s) and {seconds} second(s)"
        else:
            await ctx.message.add_reaction("❌")
            response = f"Uh oh! <@{member.id}> cannot donate more than 50.000 coins!"
    else:
        await ctx.message.add_reaction("❌")
        response = f"Uh oh! <@{member.id}> doesn't seem to have coins that much!"
    
    await ctx.send(response)

@donate.error
async def donate_error(ctx,error):
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
    else:
        await ctx.send(f"```Please type @member you want to donate and donation amount clearly. Example of proper usage:\n\n!apollo donate @Member 1000```")

@client.command('shop')
async def shop(ctx):
    embed = discord.Embed(  title="Apollo's Shop",
                            description="Welcome to Apollo's Shop! You can purchase any of these items by typing `!apollo purchase <item>`",
                            color=discord.Color.green())
    embed.add_field(name="**🍲Soup Kettle Token🍲**. Can be traded for a soup Kettle. Which you can then turn in the soup kettle for bells. Each soup kettle when given to a treasurer is worth 99,000 Bells", value="Price: 💰4.000",inline=False)
    embed.add_field(name="**🔴Foundation Token🔴**. Worth 1 stack of anything from the dodo code",value="Price: 💰12.000",inline=True)
    embed.add_field(name="**♥Heart Token♥**. Worth 3 stacks of anything from the dodo code",value="Price: 💰20.000")

    await ctx.send(embed=embed)

@client.command('purchase')
async def purchase(ctx, *, item : str):
    member = ctx.author
    item = item.lower()
    item_dict = {'soup kettle token':4000, 'foundation token':12000, 'heart token':20000}

    conn = await get_conn()
    cursor = conn.cursor()
    query_coin = "SELECT coins FROM players WHERE player_id = %s"
    data_coin = (member.id,)
    cursor.execute(query_coin,data_coin)
    result = cursor.fetchall()
    result_list = [e[0] for e in result]
    player_coin = result_list[0]

    if item in item_dict.keys():
        if player_coin > item_dict[item]:
            query_item = "INSERT INTO items (player_id,player_name,item_name,created_at,last_modified_at) VALUES (%s,%s,%s,%s,%s)"
            data_item = (member.id, member.name, item, datetime.datetime.now(), datetime.datetime.now())
            query_coin = "UPDATE players SET coins = coins - %s, last_modified_at = %s WHERE player_id = %s"
            data_coin = (item_dict[item], datetime.datetime.now(), member.id)
            cursor.execute(query_item,data_item)
            cursor.execute(query_coin, data_coin)
            conn.commit()
            conn.close()
            await ctx.message.add_reaction("✅")
            response = f"<@{member.id}> has successfully purchased `{item}` from shop!"
        else:
            await ctx.message.add_reaction("❌")
            choices = ["Hey. Buddy. You need more than what you got for that.",
            "I'm sorry but you don't have the needed coins! You could always come back when you got enough!",
            "You don't seem to have enough. Come back another time."]
            response = random.choice(choices)
    else:
        await ctx.message.add_reaction("❌")
        response = f"I'm sorry, I couldn't find `{item}` in my shop"
    
    await ctx.send(response)

@purchase.error
async def purchase_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
    else:
        await ctx.send("```Uh Oh! You need to define the item you want to purchase. Example of proper usage: \n\n!apollo exchange soup kettle token```")

@client.command('exchange')
async def exchange(ctx, *, item : str):
    member = ctx.author
    splitted_words = item.split(',')

    if (len(splitted_words) == 2):
        exchanged_item = splitted_words[0]
        exchanged_note = splitted_words[1]
        item = item.lower()
        items_dict = {'soup kettle token':'99,000 Bells', 'foundation token':'1 stack of anything from the dodo code', 'heart token':'3 stacks of anything from the dodo code'}

        conn = await get_conn()
        cursor = conn.cursor()
        query_coin = "SELECT item_name FROM items WHERE player_id = %s"
        data_coin = (member.id,)
        cursor.execute(query_coin,data_coin)
        result = cursor.fetchall()
        players_items = [e[0] for e in result]

        query_channel = "SELECT exchange_channel_id FROM servers WHERE server_id = %s"
        data_channel = (ctx.guild.id,)
        cursor.execute(query_channel,data_channel)
        result = cursor.fetchall()
        result_list = [e[0] for e in result]
        exchange_channel_id = result_list[0]
        channel = client.get_channel(exchange_channel_id)

        if exchanged_item in players_items:
            query_item = "DELETE FROM items WHERE id = (SELECT MIN(id) FROM items WHERE player_id = %s AND item_name = %s)"
            data_item = (member.id, exchanged_item)
            cursor.execute(query_item,data_item)
            conn.commit()
            conn.close()
            response = f"<@{member.id}> has turned in {exchanged_item}, if there is anyone here, please give <@{member.id}> {items_dict[exchanged_item]}"
            await channel.send(f"<@{member.id}> has turned in {exchanged_item}, if there is anyone here, please give <@{member.id}> {items_dict[exchanged_item]}\nNote: {exchanged_note}")
            await ctx.message.add_reaction("✅")
        else:
            response = f"You don't seem to have the item in question. Perhaps try another one?"
            await ctx.message.add_reaction("❌")
    else:
        response = "```Sorry, you need to add a note for your exchange. Example of proper usage:\n!apollo exchange soup kettle token, my dodo code is: 123456```"
        await ctx.message.add_reaction("❌")
    await ctx.send(response)

@exchange.error
async def exchange_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
    else:
        await ctx.send("```Uh Oh! You need to define the item you want to exchange. Example of proper usage: \n\n!apollo exchange soup kettle token```")

@client.command(name='guess',aliases=['answer'])
async def guess(ctx, guess_answer, bet_amount):
    member = ctx.author
    bet_amount = int(bet_amount)

    conn = await get_conn()
    cursor = conn.cursor()
    query_last_game = "SELECT last_card_games_name, last_card_games_answer, max_card_games_reaction_time FROM servers WHERE server_id = %s"
    data_last_game = (ctx.guild.id,)
    cursor.execute(query_last_game,data_last_game)
    result = cursor.fetchall()
    last_card_games_name = result[0][0]
    last_card_games_answer = result[0][1]
    max_card_games_reaction_time = result[0][2]

    query_player_coin = "SELECT coins FROM players WHERE player_id = %s"
    data_player_coin = (member.id,)
    cursor.execute(query_player_coin,data_player_coin)
    result = cursor.fetchall()
    result_list = [e[0] for e in result]
    player_coin = result_list[0]

    if (datetime.datetime.now() < max_card_games_reaction_time):
        if (bet_amount > 0):
            if (bet_amount <= player_coin):
                if (last_card_games_name == "GTC"):
                    if (bet_amount <= 2000):
                        if (guess_answer in ["red","black"]):
                            if (guess_answer == last_card_games_answer):
                                new_coins = bet_amount
                            else:
                                new_coins = -bet_amount
                            await ctx.message.add_reaction("✅")
                            query = "UPDATE players SET coins = coins + %s, last_card_game_answer = %s, last_card_game_bet = %s,last_card_game_answer_time = current_timestamp WHERE player_id = %s"
                            data = (new_coins, guess_answer, abs(new_coins),member.id)
                            cursor.execute(query,data)
                            conn.commit()
                            response = f"<@{member.id}> has locked their answer! Good Luck!"
                        else:
                            await ctx.message.add_reaction("❌")
                            response = f"<@{member.id}>'s answer must be black/red"
                    else:
                        await ctx.message.add_reaction("❌")
                        response = f"Sorry <@{member.id}>. You can only bet up to 2000"
                elif (last_card_games_name == "PCC"):
                    if (bet_amount <= 4000):
                        if (guess_answer in ["spade","club","diamond","heart"]):
                            if (guess_answer == last_card_games_answer):
                                new_coins = bet_amount
                            else:
                                new_coins = -bet_amount
                            await ctx.message.add_reaction("✅")
                            query = "UPDATE players SET coins = coins + %s, last_card_game_answer = %s, last_card_game_bet = %s, last_card_game_answer_time = current_timestamp WHERE player_id = %s"
                            data = (new_coins, guess_answer, abs(new_coins), member.id)
                            cursor.execute(query,data)
                            conn.commit()
                            response = f"<@{member.id}> has locked their answer! Good Luck!"
                        else:
                            await ctx.message.add_reaction("❌")
                            response = f"<@{member.id}>'s answer must be in spade/club/diamond/heart"
                    else:
                        await ctx.message.add_reaction("❌")
                        response = f"Sorry <@{member.id}>. You can only bet up to 4000"
                elif (last_card_games_name == "ACE"):
                    try:
                        guess_answer = int(guess_answer)
                    except:
                        await ctx.message.add_reaction("❌")
                        response = f"<@{member.id}>'s answer must be between 1 and 10"
                    last_card_games_answer = int(last_card_games_answer)
                    if (bet_amount <= 500000):
                        if guess_answer in range(1,11):
                            if (guess_answer == last_card_games_answer):
                                new_coins = bet_amount
                            else:
                                new_coins = -bet_amount
                            await ctx.message.add_reaction("✅")
                            query = "UPDATE players SET coins = coins + %s, last_card_game_answer = %s, last_card_game_bet = %s, last_card_game_answer_time = current_timestamp WHERE player_id = %s"
                            data = (new_coins, guess_answer, abs(new_coins), member.id)
                            cursor.execute(query,data)
                            conn.commit()
                            response = f"<@{member.id}> has locked their answer! Good Luck!"
                        else:
                            await ctx.message.add_reaction("❌")
                            response = f"<@{member.id}>'s answer must be between 1 and 10"
                    else:
                        await ctx.message.add_reaction("❌")
                        response = f"Sorry <@{member.id}>. You can only bet up to 500000"
            else:
                await ctx.message.add_reaction("❌")
                response = f"<@{member.id}> doesn't have enough coins to bet!"
        else:
            await ctx.message.add_reaction("❌")
            response = f"<@{member.id}> can't bet with negative amount of coins!"
    else:
        await ctx.message.add_reaction("❌")
        response = f"Time's up! <@{member.id}> was late to answer"
    
    conn.commit()
    conn.close()
    
    await ctx.send(response)

@guess.error
async def guess_error(ctx, error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
    else:
        await ctx.send(f"```Please input your answer and bet amount clearly. Example of proper usage: !apollo guess red 100```")

@client.command(name='leaderboard',aliases=['rank'])
async def leaderboard(ctx):
    conn = await get_conn()
    cursor = conn.cursor()
    query_rank = "SELECT player_name, coins FROM players ORDER BY coins DESC"
    cursor.execute(query_rank)
    result = cursor.fetchall()
    player_name = [e[0] for e in result]
    player_coins = [e[1] for e in result]

    response = ""
    if len(player_coins) < 10:
        for i in range(0,len(player_coins)):
            response = response + f"#{i+1} Name : **{player_name[i]}**, Coins : **{player_coins[i]}**\n"
    else:
        for i in range(0,10):
            response = response + f"#{i+1} Name : **{player_name[i]}**, Coins : **{player_coins[i]}**\n"
    
    embed = discord.Embed(title="**Apollo Games Leaderboard**", color=discord.Color.blue(),
                          description=response)
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png")

    await ctx.send(f"Alright {ctx.author.mention} please wait one minute while I tally the results...")
    await asyncio.sleep(70)
    await ctx.send(f"Here you go {ctx.author.mention}!")
    await ctx.send(embed=embed)

@client.command('guide')
async def guide(ctx):
    guide = get_guide_string()
    await ctx.send(guide)

# apollo_free_coins.start()
# apollo_card_games.start()

client.run(TOKEN)