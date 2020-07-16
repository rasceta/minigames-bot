import discord
import datetime
import random
import psycopg2

from datetime import datetime as dt

async def get_items_response(conn, member):
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
            item_response = ', '.join(items_list)
        else:
            item_response = ""
            unique_items = list(set(items_list))
            for i in unique_items:
                item_response = item_response + f"{i} ({items_list.count(i)})\n"
    except:
        pass

    embed = discord.Embed(title=f"{member.name}'s items info",
                            color=discord.Color.gold())
    embed.set_thumbnail(url="https://media.discordapp.net/attachments/729939322664517743/733134840274223155/genericcoin.png")
    embed.add_field(name="Name", value=member.name, inline=False)
    embed.add_field(name="💰Coins", value=player_coin, inline=False)
    embed.add_field(name="🎒Items", value=item_response, inline=False)
    return embed

async def get_slot_response(ctx, conn, member, slot, stars_count, bet_amount):
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
                        response_win = f"Oh, that's too bad! Poor {member.mention} landed 1 star. Here you go! **{int(bet_amount*0.4)}** coins for you!"
                        coins = int(bet_amount*0.4) - bet_amount
                    elif stars_count == 2:
                        response_win = f"Hey, not bad! {member.mention} rolled 2 stars! Take it! **{int(bet_amount*(1.3))}** coins for you!"
                        coins = int(bet_amount*(1.3)) - bet_amount
                    elif stars_count == 3:
                        response_win = f"Congratulations! {member.mention} rolled 3 stars! Amazing! **{int(bet_amount*2)}** coins for you!"
                        coins = int(bet_amount*2) - bet_amount
                    elif stars_count == 4:
                        response_win = f"Sensational! {member.mention} rolled 4 stars! What are the odds? You deserve it! **{int(bet_amount*4)}** coins for you!"
                        coins = int(bet_amount*4) - bet_amount
                    else:
                        response_win = f"Hey, there's always next time {member.mention}. Feel free to try again!"
                        coins = -bet_amount
                    
                    query = "UPDATE players SET coins = coins + %s, next_slot_time = %s, last_modified_at = %s WHERE player_id = %s"
                    next_slot_time = datetime.datetime.now() + datetime.timedelta(seconds=5)
                    data = (coins,next_slot_time, datetime.datetime.now(), member.id)
                    cursor.execute(query,data)
                    conn.commit()
                    
                    embed = discord.Embed(title="** Apollo's Slot Machine**",
                                        description="Place a bet and slot!"  )
                    embed.set_thumbnail(url="https://img.freepik.com/free-vector/slot-machine-colorful-neon-sign-machine-shape-with-triple-seven-brick-wall-background_1262-11913.jpg?size=338&ext=jpg")
                    embed.add_field(name=' | '.join(slot), value=response_win)
                    await ctx.message.add_reaction("✅")
                    return embed
                else:
                    next_slot_time = next_slot_time - datetime.datetime.now()
                    minutes = int((next_slot_time.seconds % 3600) / 60)
                    seconds = int(next_slot_time.seconds % 60)
                    await ctx.message.add_reaction("❌")
                    response = f"Uh Oh! {member.mention} can use slot machine again in {minutes}m and {seconds}s"
            else:
                await ctx.message.add_reaction("❌")
                response = f"Uh Oh! {member.mention} doesn't seem have enough coins to bet."
        else:
            await ctx.message.add_reaction("❌")
            response = f"Uh Oh! {member.mention}'s bet amount must be below 2000."
    else:
        await ctx.message.add_reaction("❌")
        response = f"Uh Oh! {member.mention} can only play slot in slot machine channel."
    return response

async def get_donate_response(ctx, conn, donater, member, donation_amount):
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
        if (donation_amount <= 100000):
            if (datetime.datetime.now() > next_donate_time):
                if (datetime.datetime.now() > next_donation_time):
                    query_donater = "UPDATE players SET coins = coins - %s, next_donate_time = %s, last_modified_at = %s where player_id = %s"
                    next_donate_time = datetime.datetime.now() + datetime.timedelta(seconds=2)
                    data_donater = (donation_amount, next_donate_time, datetime.datetime.now(), donater.id)
                    cursor.execute(query_donater, data_donater)
                    query_donate_to = "UPDATE players SET coins = coins + %s, next_donation_time = %s, last_modified_at = %s where player_id = %s"
                    next_donation_time = datetime.datetime.now() + datetime.timedelta(seconds=2)
                    data_donate_to = (donation_amount, next_donation_time, datetime.datetime.now(), member.id)
                    cursor.execute(query_donate_to, data_donate_to)
                    conn.commit()
                    await ctx.message.add_reaction("✅")
                    response = f"{donater.mention} Successfully donated {donation_amount} coins to {member.mention}"
                else:
                    next_donation_time = next_donation_time - datetime.datetime.now()
                    minutes = int((next_donation_time.seconds % 3600) / 60)
                    hours = int(next_donation_time.seconds / 3600)
                    seconds = int(next_donation_time.seconds % 60)
                    await ctx.message.add_reaction("❌")
                    response = f"Donation failed. {member.mention} will be able to be donated in {hours} hour(s) {minutes} minute(s) and {seconds} second(s)"
            else:
                next_donate_time = next_donate_time - datetime.datetime.now()
                minutes = int((next_donate_time.seconds % 3600) / 60)
                hours = int(next_donate_time.seconds / 3600)
                seconds = int(next_donate_time.seconds % 60)
                await ctx.message.add_reaction("❌")
                response = f"Donation failed. {donater.mention} will be able to donate in {hours} hour(s) {minutes} minute(s) and {seconds} second(s)"
        else:
            await ctx.message.add_reaction("❌")
            response = f"Uh oh! {donater.mention} cannot donate more than 100,000 coins!"
    else:
        await ctx.message.add_reaction("❌")
        response = f"Uh oh! {donater.mention} doesn't seem to have that much coins!"
    return response

async def get_guess_response(ctx, conn, member, guess_answer, bet_amount):
    cursor = conn.cursor()
    query_last_game = "SELECT last_card_games_name, last_card_games_answer, max_card_games_reaction_time FROM servers WHERE server_id = %s"
    data_last_game = (ctx.guild.id,)
    cursor.execute(query_last_game,data_last_game)
    result = cursor.fetchall()
    last_card_games_name = result[0][0]
    last_card_games_answer = result[0][1]
    max_card_games_reaction_time = result[0][2]

    query_player_coin = "SELECT coins, last_card_game_answer_time FROM players WHERE player_id = %s"
    data_player_coin = (member.id,)
    cursor.execute(query_player_coin,data_player_coin)
    result = cursor.fetchall()
    player_coin = result[0][0]
    last_card_game_answer_time = result[0][1]

    if last_card_game_answer_time == None:
        last_card_game_answer_time = datetime.datetime.now() - datetime.timedelta(minutes=5)

    if (datetime.datetime.now() < max_card_games_reaction_time):
        if (datetime.datetime.now() > last_card_game_answer_time + datetime.timedelta(minutes=1)) :
            if (bet_amount <= player_coin):
                if (bet_amount > 0):
                    if (last_card_games_name == "GTC"):
                        if (bet_amount <= 2000):
                            if (guess_answer in ["red","black"]):
                                if (guess_answer == last_card_games_answer):
                                    new_coins = bet_amount
                                else:
                                    new_coins = -bet_amount
                                await ctx.message.add_reaction("✅")
                                query = "UPDATE players SET coins = coins + %s, last_card_game_answer = %s, last_card_game_bet = %s,last_card_game_answer_time = current_timestamp, last_modified_at = current_timestamp WHERE player_id = %s"
                                data = (new_coins, guess_answer, abs(new_coins),member.id)
                                cursor.execute(query,data)
                                conn.commit()
                                response = f"{member.mention} has locked their answer! Good Luck!"
                            else:
                                await ctx.message.add_reaction("❌")
                                response = f"{member.mention}'s answer must be black/red"
                        else:
                            await ctx.message.add_reaction("❌")
                            response = f"Sorry {member.mention}. You can only bet up to 2000"
                    elif (last_card_games_name == "PCC"):
                        if (bet_amount <= 4000):
                            if (guess_answer in ["spade","club","diamond","heart"]):
                                if (guess_answer == last_card_games_answer):
                                    new_coins = bet_amount
                                else:
                                    new_coins = -bet_amount
                                await ctx.message.add_reaction("✅")
                                query = "UPDATE players SET coins = coins + %s, last_card_game_answer = %s, last_card_game_bet = %s, last_card_game_answer_time = current_timestamp, last_modified_at = current_timestamp WHERE player_id = %s"
                                data = (new_coins, guess_answer, abs(new_coins), member.id)
                                cursor.execute(query,data)
                                conn.commit()
                                response = f"{member.mention} has locked their answer! Good Luck!"
                            else:
                                await ctx.message.add_reaction("❌")
                                response = f"{member.mention}'s answer must be in spade/club/diamond/heart"
                        else:
                            await ctx.message.add_reaction("❌")
                            response = f"Sorry {member.mention}. You can only bet up to 4000"
                    elif (last_card_games_name == "ACE"):
                        try:
                            guess_answer = int(guess_answer)
                        except:
                            await ctx.message.add_reaction("❌")
                            response = f"{member.mention}'s answer must be between 1 and 10"
                        last_card_games_answer = int(last_card_games_answer)
                        if (bet_amount <= 20000):
                            if guess_answer in range(1,11):
                                if (guess_answer == last_card_games_answer):
                                    new_coins = bet_amount * 3
                                else:
                                    new_coins = -bet_amount
                                await ctx.message.add_reaction("✅")
                                query = "UPDATE players SET coins = coins + %s, last_card_game_answer = %s, last_card_game_bet = %s, last_card_game_answer_time = current_timestamp, last_modified_at = current_timestamp WHERE player_id = %s"
                                data = (new_coins, guess_answer, abs(bet_amount), member.id)
                                cursor.execute(query,data)
                                conn.commit()
                                response = f"{member.mention} has locked their answer! Good Luck!"
                            else:
                                await ctx.message.add_reaction("❌")
                                response = f"{member.mention}'s answer must be between 1 and 10"
                        else:
                            await ctx.message.add_reaction("❌")
                            response = f"Sorry {member.mention}. You can only bet up to 20000"
                else:
                    await ctx.message.add_reaction("❌")
                    response = f"{member.mention} can't bet with negative amount of coins!"
            else:
                await ctx.message.add_reaction("❌")
                response = f"{member.mention} doesn't have enough coins to bet!"
        else:
            await ctx.message.add_reaction("❌")
            response = f"Uh Oh! {member.mention}, you can only guess once!"
    else:
        await ctx.message.add_reaction("❌")
        response = f"Time's up! {member.mention} was late to answer"
    
    conn.commit()
    
    return response