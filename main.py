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

from players_commands import get_items_response, get_slot_response, get_donate_response, get_guess_response

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

    for channel in client.get_all_channels():
        if channel.id in free_coins_channel_id_list:

            rand_num = random.randint(1,10)
            if rand_num <= 8:
                free_coins_amount = 200
                img_url = "https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png"
                footer_text = "React with the 👍 reaction! Quickly! I must go in 40 seconds!"
            else:
                free_coins_amount = 1000
                img_url = "https://cdn.discordapp.com/attachments/717658774265004052/726036484657774603/coins3.png"
                footer_text = "This time I'm bringing in 1,000 coins for everyone! Hurry and react with 👍!"
            embed = discord.Embed(title="Free Coins",
                                description=f"Hello, hello! The mysterious coin creature's here. It has returned for all to see! It's here to give you all free coins! Yes! You heard that right! Free coins!")
            embed.set_thumbnail(url=img_url)
            embed.set_footer(text=footer_text)
            new_message = await channel.send(embed=embed)
            await new_message.add_reaction("👍")
            max_reaction_time = datetime.datetime.now() + datetime.timedelta(seconds=40)

            query = "UPDATE servers SET last_free_coins_message_id = %s, max_free_coins_reaction_time = %s, free_coins_amount = %s WHERE free_coins_channel_id = %s"
            data = (new_message.id, max_reaction_time, free_coins_amount, channel.id)
            cursor.execute(query,data)
            conn.commit()
            
    conn.close()

    embed = discord.Embed(title="Free Coins",
                        description="I must go now! Toodle doo~ I'll be back whenever!")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/723924559446802502/coins2.png")
    embed.set_footer(text="In the meantime! Please check out #community features!")
    await asyncio.sleep(40)
    for channel in client.get_all_channels():
        if channel.id in free_coins_channel_id_list:
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

    for channel in client.get_all_channels():
        if channel.id in card_game_channel_id_list:
            new_message = await channel.send(embed=embed)
            max_card_games_reaction_time = datetime.datetime.now() + datetime.timedelta(minutes=1)

            query = "UPDATE servers SET last_card_games_name = %s, last_card_games_answer = %s, last_card_games_message_id = %s, max_card_games_reaction_time = %s, last_modified_at = %s WHERE card_game_channel_id = %s"
            data = (game_name, answer, new_message.id, max_card_games_reaction_time, datetime.datetime.now(), channel.id)
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
                if game_name == "ACE":
                    players_won = players_won + f"\n**{player_name[i]}** won **{player_bets[i]*4}**"
                else:
                    players_won = players_won + f"\n**{player_name[i]}** won **{player_bets[i]*2}**"

        game_outro = get_card_game_outro(game_name,answer)
        embed = discord.Embed(title=game_outro[0],description=game_outro[1],color=discord.Color.blue())
        embed.set_image(url=game_outro[2])
        embed.set_thumbnail(url="http://clipart-library.com/images/pT5o6baac.jpg")
        embed.add_field(name="**Winners**",value=players_won)

        for channel in client.get_all_channels():
            if channel.id in card_game_channel_id_list:
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
    channel_id = payload.channel_id
    channel = client.get_channel(channel_id)

    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT last_free_coins_message_id, max_free_coins_reaction_time, free_coins_amount from servers WHERE server_id = %s"
    data = (guild_id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    last_message_id = result[0][0]
    max_reaction_time = result[0][1]
    free_coins_amount = result[0][2]
    try:
        if (message_id == last_message_id) and (user_id != 721001236589183070):
            time_now = datetime.datetime.now()
            if time_now <= max_reaction_time:
                if payload.emoji.name == '👍':
                    query = "UPDATE players SET coins = coins + %s WHERE player_id = %s"
                    data = (free_coins_amount,user_id)
                    cursor.execute(query,data)
                    conn.commit()
            else:
                pass
    except:
        print('Max free coins reaction time is not set')

    query_last_count = "SELECT last_count_member_id, last_count_message_id, last_count_fee, last_count_status, last_count_member_pay, max_count_game_reaction_time FROM count_game WHERE server_id = %s"
    cursor.execute(query_last_count, (guild_id,))
    result = cursor.fetchall()
    last_count_member_id = result[0][0]
    last_count_message_id = result[0][1]
    last_count_fee = result[0][2]
    last_count_status = result[0][3]
    last_count_member_pay = result[0][4]
    max_count_game_reaction_time = result[0][5]

    try:
        query_coin = "SELECT coins FROM players WHERE player_id = %s"
        cursor.execute(query_coin, (user_id,))
        result = cursor.fetchall()
        player_coin = result[0][0]
    except:
        player_coin = 0

    try:
        if message_id == last_count_message_id:
            if user_id == last_count_member_id:
                if last_count_status == "bad":
                    if payload.emoji.name == "💰":
                        if player_coin == 0 or player_coin < last_count_fee:
                            response = f"It seems {payload.member.mention} doesn't have enough coins! If somebody else wants to pay the fee, please react with 💰 on their failed count message!"
                            query_update_count = "UPDATE count_game SET last_count_member_pay = %s, last_modified_at = current_timestamp WHERE server_id = %s"
                            data_update_count = ("no", guild_id)
                            cursor.execute(query_update_count, data_update_count)
                            conn.commit()
                        else:
                            query_update_player = "UPDATE players SET coins = coins - %s, last_modified_at = current_timestamp WHERE player_id = %s"
                            data_update_player = (last_count_fee, user_id)
                            query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_status = %s, last_count_member_pay = %s, last_count_fee = last_count_fee * 2, total_fee = total_fee + last_count_fee, last_modified_at = current_timestamp WHERE server_id = %s"
                            data_update_count = ("good", "yes", guild_id)
                            cursor.execute(query_update_player, data_update_player)
                            conn.commit()
                            cursor.execute(query_update_count, data_update_count)
                            conn.commit()
                            response = f"{payload.member.mention} has decided to pay with their coins! The count resumes! Have fun!"
                            print('continue count')
                    elif payload.emoji.name == "🔁":
                        query_update_count = "UPDATE count_game SET last_count_member_pay = %s, last_count_member_id = 1, last_modified_at = current_timestamp WHERE server_id = %s"
                        data_update_count = ("wait", guild_id)
                        cursor.execute(query_update_count, data_update_count)
                        conn.commit()
                        response = f"It seems {payload.member.mention} wants to start over!\nReact with 🔁 if you wish you start over \nor, react with 💰 if you wish to continue on their failed count message!\nBut remember, you need to pay the fine of {last_count_fee}"
                        print('restart count')
            elif (last_count_member_pay == "no") or ((last_count_member_pay == "wait") and (datetime.datetime.now() >= max_count_game_reaction_time)):
                if payload.emoji.name == "💰":
                    if player_coin == 0 or player_coin < last_count_fee:
                        response = f"Uh oh, well, it seems {payload.member.mention} also doesn't have enough money! Oh well! We'll just have to start from 1! Have fun!"
                        query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_number = 0, last_count_status = %s, last_count_fee = 300, last_count_member_pay = %s, last_modified_at = current_timestamp WHERE server_id = %s"
                        data_update_count = ("good", "yes", guild_id)
                        cursor.execute(query_update_count, data_update_count)
                        conn.commit()
                        print('restart count')
                    else:
                        query_update_player = "UPDATE players SET coins = coins - %s, last_modified_at = current_timestamp WHERE player_id = %s"
                        data_update_player = (last_count_fee, user_id)
                        query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_status = %s, last_count_member_pay = %s, last_count_fee = last_count_fee * 2, total_fee = total_fee + last_count_fee, last_modified_at = current_timestamp WHERE server_id = %s"
                        data_update_count = ("good", "yes", guild_id)
                        cursor.execute(query_update_player, data_update_player)
                        conn.commit()
                        cursor.execute(query_update_count, data_update_count)
                        conn.commit()
                        response = f"{payload.member.mention} has decided to pay with their coins! The count resumes! Have fun!"
                        print('continue count')
                elif payload.emoji.name == "🔁":
                    response = f"Uh oh, well, it seems {payload.member.mention} also wants to start over! Oh well! We'll just have to start from 1! Have fun!"
                    query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_number = 0, last_count_status = %s, last_count_fee = 300, last_count_member_pay = %s, last_modified_at = current_timestamp WHERE server_id = %s"
                    data_update_count = ("good", "yes", guild_id)
                    cursor.execute(query_update_count, data_update_count)
                    conn.commit()
                    print('restart count')
            embed = discord.Embed(title="Apollo's Chain Counting Game", description=response, color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/726063162364919818/nf67.png")
            await channel.send(embed=embed)
    except Exception as e:
        print(e)


    conn.close()

@client.event
async def on_raw_reaction_remove(payload):
    user_id = payload.user_id
    message_id = payload.message_id
    guild_id = payload.guild_id

    conn = await get_conn()
    cursor = conn.cursor()
    query = "SELECT last_free_coins_message_id, max_free_coins_reaction_time, free_coins_amount from servers WHERE server_id = %s"
    data = (guild_id,)
    cursor.execute(query,data)
    result = cursor.fetchall()
    last_message_id = result[0][0]
    max_reaction_time = result[0][1]
    free_coins_amount = result[0][2]
    try:
        if message_id == last_message_id:
            time_now = datetime.datetime.now()
            if time_now <= max_reaction_time:
                if payload.emoji.name == '👍':
                    query = "UPDATE players SET coins = coins - %s WHERE player_id = %s"
                    data = (free_coins_amount,user_id)
                    cursor.execute(query,data)
                    conn.commit()
                    conn.close()
            else:
                pass
    except:
        print('Max free coins reaction time is not set')

@client.event
async def on_message(message):
    conn = await get_conn()
    cursor = conn.cursor()
    try: # insert new row to servers table if not exist
        query = "INSERT INTO servers(server_id,server_name,created_at, last_modified_at) VALUES(%s,%s,%s,%s)"
        data = (message.guild.id, message.guild.name, datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query,data)
    except:
        pass
    conn.commit()

    try:
        query_count = "SELECT count_game_channel_id, last_count_number, last_count_member_id, last_count_status, last_count_fee from count_game where server_id = %s"
        data_count = (message.guild.id, )
        cursor.execute(query_count,data_count)
        result = cursor.fetchall()
        count_game_channel_id = result[0][0]
        last_count_number = result[0][1]
        last_count_member_id = result[0][2]
        last_count_status = result[0][3]
        last_count_fee = result[0][4]
        try:
            content = int(message.content)
        except:
            content = ""
        if (message.channel.id == count_game_channel_id) and (message.author.bot is False):
            if last_count_status == 'good':
                if isinstance(content, int):
                    if content == last_count_number + 1:
                        if message.author.id != last_count_member_id:
                            await message.add_reaction("✅")
                            failed_count = False
                            if (last_count_number + 1) % 1000 == 0:
                                coins = 100000
                                response = f"Awesome! **{last_count_number + 1}** ! Here's {int(coins)} coins for you, {message.author.mention}"
                            elif (last_count_number + 1) % 500 == 0:
                                coins = 50000
                                response = f"Great! **{last_count_number + 1}** ! Here's {int(coins)} coins for you, {message.author.mention}"
                            elif (last_count_number + 1) % 100 == 0:
                                coins = 12000
                                response = f"Nice! **{last_count_number + 1}** ! Here's {int(coins)} coins for you, {message.author.mention}"
                            else:
                                coins = 0
                            query = "UPDATE count_game SET last_count_member_id = %s, last_count_number = %s, last_modified_at = current_timestamp where server_id = %s"
                            data = (message.author.id, content, message.guild.id)
                            cursor.execute(query,data)
                            conn.commit()

                            query_coin = "UPDATE players SET coins = coins + %s, last_modified_at = current_timestamp WHERE player_id = %s"
                            data_coin = (coins, message.author.id)
                            cursor.execute(query_coin, data_coin)
                            conn.commit()
                        else:
                            print('same member')
                            failed_count = True
                            query = "UPDATE count_game SET last_count_member_id = %s, last_count_message_id = %s, last_count_status = %s, last_count_member_pay = %s, max_count_game_reaction_time = %s, last_modified_at = current_timestamp where server_id = %s"
                            data = (message.author.id, message.id, "bad", "wait", datetime.datetime.now() + datetime.timedelta(seconds=15), message.guild.id)
                            cursor.execute(query,data)
                            conn.commit()
                            await message.add_reaction("❌")
                            await message.add_reaction("💰")
                            await message.add_reaction("🔁")
                            response = f"Oh no! {message.author.mention} broke the chain. (**{content}**)!\nYou could react with 💰 to pay a small fine of **{last_count_fee}** coins in order to continue the game!\nOr, if you wish to restart, simply react to the 🔁 and start all over again from 1!"
                    else:
                        print('wrong number')
                        failed_count = True
                        query = "UPDATE count_game SET last_count_member_id = %s, last_count_message_id = %s, last_count_status = %s, last_count_member_pay = %s, max_count_game_reaction_time = %s, last_modified_at = current_timestamp where server_id = %s"
                        data = (message.author.id, message.id, "bad", "wait", datetime.datetime.now() + datetime.timedelta(seconds=15),message.guild.id)
                        cursor.execute(query,data)
                        conn.commit()
                        await message.add_reaction("❌")
                        await message.add_reaction("💰")
                        await message.add_reaction("🔁")
                        response = f"Oh no! {message.author.mention} broke the chain. (**{content}**)!\nYou could react with 💰 to pay a small fine of **{last_count_fee}** coins in order to continue the game!\nOr, if you wish to restart, simply react to the 🔁 and start all over again from 1!"
                else:
                    print('Normal chat (count game)')
            else:
                print('status bad')
                await message.delete()
            embed = discord.Embed(title="Apollo's Chain Counting Game", description=response, color=discord.Color.purple())
            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/726063162364919818/nf67.png")
            if failed_count:
                embed.add_field(name="Note",value="Only the player, who has broken the chain, can react. If there are no reactions within 15 seconds, it is then open for other players to react with 💰 on their failed count message.")
            await message.channel.send(embed=embed)
    except Exception as e:
        print(e)
    conn.close()
    await client.process_commands(message)

@commands.has_permissions(administrator=True)
@client.command()
async def clear(ctx, limits=5):
    await ctx.channel.purge(limit=limits)

@commands.has_permissions(administrator=True)
@client.command('set_channel')
async def set_channel(ctx, alias, channel: discord.TextChannel):
    aliases = ['coins','exchange','slot','cards']
    conn = await get_conn()
    cursor = conn.cursor()
    if alias in ['coins','exchange','card','slot','count']:
        if alias == 'coins':
            query = "UPDATE servers SET free_coins_channel_id = %s WHERE server_id = %s"
        elif alias == 'exchange':
            query = "UPDATE servers SET exchange_channel_id = %s WHERE server_id = %s"
        elif alias == 'card':
            query = "UPDATE servers SET card_game_channel_id = %s WHERE server_id = %s"
        elif alias == 'slot':
            query = "UPDATE servers SET slot_game_channel_id = %s WHERE server_id = %s"
        data = (channel.id, ctx.guild.id)
        cursor.execute(query, data)
        conn.commit()
        conn.close()
        await ctx.message.add_reaction("✅")
        print(f"Updated {alias} channel (set_channel)")
        await ctx.send(f"You have set {channel.mention} as `{alias} Channel`")
    else:
        await ctx.message.add_reaction("❌")
        await ctx.send(f"Uh Oh! You need to put an alias like {'/'.join(aliases)} and #channel you want to set")

@set_channel.error
async def set_channel_error(ctx, error):
    aliases = ['coins','exchange','slot','cards','count']
    await ctx.message.add_reaction("❌")
    await ctx.send(error)
    await ctx.send(f"Uh Oh! You need to put an alias like {'/'.join(aliases)} and #channel you want to set")

@commands.has_permissions(administrator=True)
@client.command('start_count')
async def start_count(ctx, channel : discord.TextChannel):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET count_game_channel_id = %s WHERE server_id = %s"
    cursor.execute(query,(channel.id, ctx.guild.id))
    conn.commit()
    try: # insert new row into count_game if not exist
        query_insert = "INSERT INTO count_game(server_id, count_game_channel_id, last_count_member_id, last_count_number, last_count_status, last_count_fee, total_fee, created_at, last_modified_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        data_insert = (ctx.guild.id, channel.id, 1, 0, 'good', 300, 0, datetime.datetime.now(), datetime.datetime.now())
        cursor.execute(query_insert,data_insert)
    except:
        conn.commit()
        query_update = "UPDATE count_game SET count_game_channel_id = %s, last_count_member_id = 1, last_count_number = %s, last_count_status = %s, last_count_fee = 300, total_fee = 0, last_modified_at = current_timestamp WHERE server_id = %s"
        data_update = (channel.id, 0, "good", ctx.guild.id)
        cursor.execute(query_update, data_update)
    conn.commit()
    await ctx.message.add_reaction("✅")
    print("Updated channel count (start_count)")
    embed = discord.Embed(title="Apollo's Chain Counting Game", description="Alright! Let's start all over again!", color=discord.Color.purple())
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/717658774265004052/726063162364919818/nf67.png")
    await channel.send(embed=embed)

@start_count.error
async def start_count_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.MissingRequiredArgument):
        response = f"```You need to define #channel you want to use for counting game. Example of proper usage:\n\n!apollo start_channel #apollo-count```"
    else:
        response = error
    await ctx.send(response)

@commands.has_permissions(administrator=True)
@client.command('stop_count')
async def stop_count(ctx):
    conn = await get_conn()
    cursor = conn.cursor()
    query = "UPDATE servers SET count_game_channel_id = %s WHERE server_id = %s"
    cursor.execute(query,(1, ctx.guild.id))
    conn.commit()
    try: # insert new row into count_game if not exist
        query_update = "UPDATE count_game SET count_game_channel_id = %s WHERE server_id = %s"
        data_update = (1, ctx.guild.id)
        cursor.execute(query_update, data_update)
        conn.commit()
        print("Updated channel count (stop_count)")
        response = f"```You have successfully stopped current chain counting game```"
    except:
        response = f"```You haven't set a channel as count channel```"
    
    await ctx.send(response)

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
    if task_name in ['card','coins']:
        if task_name == "card":
            apollo_card_games.start()
        elif task_name == "coins":
            apollo_free_coins.start()
        await ctx.message.add_reaction("✅")
        await ctx.author.send(f"{task_name} has successfully started.")

@commands.has_permissions(administrator=True)
@client.command('stop')
async def stop(ctx, *, task_name: str):
    if task_name in ['card','coins']:
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
    if not isinstance(error, commands.MissingRole):
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

    if bet_amount > 0:
        response = await get_slot_response(ctx, conn, member, slot, stars_count, bet_amount)
    else:
        await ctx.message.add_reaction("❌")
        response = f"Uh Oh! {ctx.author.mention} cannot bet with negative amount of coins"

    if isinstance(response, discord.Embed):
        await ctx.send(embed=response)
    else:
        await ctx.send(response)

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
    embed = await get_items_response(conn,member)
    await ctx.send(embed=embed)

@items.error
async def items_error(ctx,error):
    try:
        if isinstance(error, commands.CommandInvokeError):
            await ctx.message.add_reaction("❌")
            await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
        elif isinstance(error, commands.MissingRole) or isinstance(error, commands.MissingRequiredArgument):
            member = ctx.author
            conn = await get_conn()
            cursor = conn.cursor()
            query_coin = "SELECT last_card_game_answer_time FROM players where player_id = %s"
            data_coin = (member.id,)
            cursor.execute(query_coin,data_coin)
            result = cursor.fetchall()
            player_answer_time = result[0][0]

            if (player_answer_time == None) or (datetime.datetime.now() > player_answer_time + datetime.timedelta(minutes=1)):
                embed = await get_items_response(conn, member)
                await ctx.send(embed=embed)
            else:
                await ctx.message.add_reaction("❌")
                await ctx.send(f"Uh Oh! {member.mention} you can check your wallet 1 minute after locking in an answer!")
    except IndexError:
        await ctx.message.add_reaction("❌")
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")

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
            if discord.utils.get(member.roles, name="Giver") is not None:
                free_coins = 24000
            elif discord.utils.get(member.roles, name="Donor") is not None:
                free_coins = 3500
            elif (discord.utils.get(member.roles, name="Members") is not None) or (discord.utils.get(member.roles, name="Explorer") is not None):
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
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"{ctx.author.mention} you can't claim your daily rewards because you have not registered! Please type `!apollo register`")

@commands.has_any_role('Giver','Donor')
@client.command('weekly')
async def weekly(ctx):
    member = ctx.author
    conn = await get_conn()
    cursor = conn.cursor()
    query_weekly = "SELECT next_weekly_coins_time FROM players where player_id = %s"
    data_weekly = (member.id,)
    cursor.execute(query_weekly,data_weekly)
    result = cursor.fetchall()
    next_weekly_coins = [e[0] for e in result]
    next_weekly_coins = next_weekly_coins[0]

    if isinstance(next_weekly_coins, datetime.datetime):
        if (datetime.datetime.now () > next_weekly_coins):
            if discord.utils.get(member.roles, name="Giver") is not None:
                free_coins = 100000
            elif discord.utils.get(member.roles, name="Donor") is not None:
                free_coins = 15000
            query = "UPDATE players SET coins = coins + %s, next_weekly_coins_time = %s where player_id = %s"
            next_weekly_coins = datetime.datetime.now() + datetime.timedelta(weeks=1)
            data = (free_coins, next_weekly_coins, member.id)
            cursor.execute(query, data)
            await ctx.message.add_reaction("✅")
            await ctx.send(f"You have claimed your weekly coins, {ctx.author.mention}. Don't forget next week!")
        else:
            next_weekly_coins = next_weekly_coins - datetime.datetime.now()
            days = int(next_weekly_coins.days)
            minutes = int((next_weekly_coins.seconds % 3600) / 60)
            hours = int(next_weekly_coins.seconds / 3600)
            seconds = int(next_weekly_coins.seconds % 60)
            await ctx.message.add_reaction("❌")
            await ctx.send(f"{ctx.author.mention}, you still have {days} day(s) {hours} hour(s) {minutes} minute(s) and {seconds} second(s) before your next weekly reward!")
    conn.commit()
    conn.close()

@weekly.error
async def weekly_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"{ctx.author.mention} you can't claim your weekly rewards because you have not registered! Please type `!apollo register`")
    elif isinstance(error, commands.MissingAnyRole):
        await ctx.send(f"Sorry, this command can only be used by `Donor` and `Giver` role")

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

@commands.has_permissions(administrator=True)
@client.command('reset_weekly')
async def reset_weekly(ctx):
    conn = await get_conn()
    cursor = conn.cursor()

    query = "UPDATE players SET next_weekly_coins_time = current_timestamp"
    cursor.execute(query)
    conn.commit()
    conn.close()
    await ctx.message.add_reaction("✅")
    await ctx.send("All players free weekly coins has been reset to now")

@client.command('donate')
async def donate(ctx, member : discord.User, donation_amount : int):
    donater = ctx.author

    conn = await get_conn()
    if donation_amount > 0:
        response = await get_donate_response(ctx,conn,donater,member,donation_amount)
    else:
        await ctx.message.add_reaction("❌")
        response = f"Uh Oh! {ctx.author.mention} cannot donate with negative amount of coins"
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
    embed.add_field(name="**🍲Soup Kettle Token🍲**. Can be traded for a soup Kettle. Which you can then turn in the soup kettle for bells. Each soup kettle when given to a treasurer is worth 99,000 Bells", value="Price: 💰4.000", inline=False)
    embed.add_field(name="**🔴Foundation Token🔴**. Worth 1 stack of anything from the dodo code", value="Price: 💰12.000", inline=True)
    embed.add_field(name="**♥Heart Token♥**. Worth 3 stacks of anything from the dodo code", value="Price: 💰20.000")
    embed.add_field(name="**💖Love Token💖**. By buying this token you are entitled to a 15 stacks of items randomly chosen from our 'free stuff' category!", value="Price: 💰100.000", inline=False)
    embed.add_field(name="**🎲Gambler🎲**. Purchasing this role signifies your dedication as a gambler, and not only do you have the fiery spirit of one, but you also have the coins to back it up!", value="Price: 💰20.000", inline=False)
    embed.add_field(name="**🤑Wealthy🤑**. Purchasing this role means you have an ample amount of coins at your disposal! The role is permanent and everyone can see exactly how wealthy you are.", value="Price: 💰200.000", inline=True)
    embed.add_field(name="Notes",value="If you want to turn in your items! Please use `!apollo exchange <item>, <dodo code>`. **Please be sure to open your island before turning in a token!**",inline=False)

    await ctx.send(embed=embed)

@client.command(name='purchase',aliases=['buy'])
async def purchase(ctx, *, item : str):
    member = ctx.author
    item = item.lower()
    item_dict = {'soup kettle token':4000, 'foundation token':12000, 'heart token':20000, 'love token':100000, 'gambler':20000, 'wealthy':200000}

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
            has_role = False
            if item not in ["gambler", "wealthy"]:
                query_item = "INSERT INTO items (player_id,player_name,item_name,created_at,last_modified_at) VALUES (%s,%s,%s,%s,%s)"
                data_item = (member.id, member.name, item, datetime.datetime.now(), datetime.datetime.now())
                query_coin = "UPDATE players SET coins = coins - %s, last_modified_at = %s WHERE player_id = %s"
                data_coin = (item_dict[item], datetime.datetime.now(), member.id)
                cursor.execute(query_item,data_item)
                conn.commit()
                cursor.execute(query_coin, data_coin)
                conn.commit()
            elif item in ["gambler","wealthy"]:
                if discord.utils.get(member.roles, name=item.title()) is not None:
                    has_role = True
                else:
                    query_coin = "UPDATE players SET coins = coins - %s, last_modified_at = %s WHERE player_id = %s"
                    data_coin = (item_dict[item], datetime.datetime.now(), member.id)
                    cursor.execute(query_coin, data_coin)
                    conn.commit()
                    await member.add_roles(discord.utils.get(member.guild.roles, name=item.title()))
            
            if has_role is False:
                await ctx.message.add_reaction("✅")
                response = f"{member.mention} has successfully purchased `{item}` from shop!"
            else:
                await ctx.message.add_reaction("❌")
                response = f"{member.mention}, You already have the {item.title()} role!"
        else:
            await ctx.message.add_reaction("❌")
            choices = ["Hey. Buddy. You need more than what you got for that.",
            "I'm sorry but you don't have the needed coins! You could always come back when you got enough!",
            "You don't seem to have enough. Come back another time."]
            response = random.choice(choices)
    else:
        await ctx.message.add_reaction("❌")
        response = f"I'm sorry, I couldn't find `{item}` in my shop"
    conn.close()
    await ctx.send(response)

@purchase.error
async def purchase_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
        await ctx.send(error)
    else:
        await ctx.send("```Uh Oh! You need to define the item you want to purchase. Example of proper usage: \n\n!apollo exchange soup kettle token```")

@client.command('exchange')
async def exchange(ctx, *, item : str):
    member = ctx.author
    splitted_words = item.split(',')

    try:
        if (len(splitted_words) == 2):
            exchanged_item = splitted_words[0]
            exchanged_note = splitted_words[1]
            item = item.lower()
            items_dict = {'soup kettle token':'99,000 Bells', 'foundation token':'1 stack of anything from the dodo code', 
                        'heart token':'3 stacks of anything from the dodo code', 'love token':'15 stacks of anything from the dodo code'}

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
                response = f"{member.mention} has turned in `{exchanged_item}`, if there is anyone here, please give {member.mention} {items_dict[exchanged_item]}"
                await channel.send(f"{member.mention} has turned in `{exchanged_item}`, if there is anyone here, please give {member.mention} {items_dict[exchanged_item]}\nNote: {exchanged_note}")
                await ctx.message.add_reaction("✅")
            else:
                response = f"You don't seem to have the item in question. Perhaps try another one?"
                await ctx.message.add_reaction("❌")
        else:
            response = "```Sorry, you need to add a note for your exchange. Example of proper usage:\n\n!apollo exchange soup kettle token, my dodo code is: 123456```"
            await ctx.message.add_reaction("❌")
    except:
        pass
    await ctx.send(response)

@exchange.error
async def exchange_error(ctx,error):
    await ctx.message.add_reaction("❌")
    if isinstance(error, commands.CommandInvokeError):
        await ctx.send(f"Uh Oh! Looks like {ctx.author.mention} haven't registered yet. Please register using `!apollo register`")
        await ctx.send(error)
    else:
        await ctx.send("```Uh Oh! You need to define the item you want to exchange. Example of proper usage: \n\n!apollo exchange soup kettle token```")

@client.command(name='guess',aliases=['answer'])
async def guess(ctx, guess_answer, bet_amount):
    member = ctx.author
    bet_amount = int(bet_amount)

    conn = await get_conn()
    
    if bet_amount >= 0:
        response = await get_guess_response(ctx,conn,member,guess_answer,bet_amount)
    else:
        await ctx.message.add_reaction("❌")
        response = f"Uh Oh! {ctx.author.mention} cannot bet with negative amount of coins"
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
    await ctx.message.add_reaction("✅")
    await ctx.send(f"Alright {ctx.author.mention} please wait one minute while I tally the results...")
    await asyncio.sleep(70)

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

    await ctx.send(f"Here you go {ctx.author.mention}!")
    await ctx.send(embed=embed)

@client.command('guide')
async def guide(ctx):
    guide = get_guide_string()
    await ctx.send(guide)

client.run(TOKEN)