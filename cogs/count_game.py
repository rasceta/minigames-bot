import discord
import asyncio
import random
import datetime
import util

from discord.ext import commands

class CountGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        member = payload.member
        conn = self.bot.conn
        message_id = payload.message_id
        guild_id = payload.guild_id

        cursor = conn.cursor()
        query_count = "SELECT last_count_message_id from count_game WHERE server_id = %s"
        data_count = (guild_id,)
        cursor.execute(query_count,data_count)
        result = cursor.fetchall()
        if len(result) > 0:
            last_count_message_id = result[0][0]
        else:
            last_count_message_id = None

        if message_id == last_count_message_id:
            channel = self.bot.get_channel(payload.channel_id)

            query_last_count = "SELECT last_count_member_id, last_count_fee, last_count_status, max_count_game_reaction_time FROM count_game WHERE server_id = %s"
            cursor.execute(query_last_count, (payload.guild_id,))
            result = cursor.fetchall()
            last_count_member_id = result[0][0]
            last_count_fee = result[0][1]
            last_count_status = result[0][2]
            max_count_game_reaction_time = result[0][3]

            try:
                query_coin = "SELECT coins FROM players WHERE player_id = %s"
                cursor.execute(query_coin, (payload.user_id,))
                result = cursor.fetchall()
                player_coin = result[0][0]
            except:
                player_coin = 0

            if last_count_status != "bad":
                return

            last_count_multiplier = random.choice((1,3))
            is_restart = False

            response = None
            if payload.user_id == last_count_member_id:
                if payload.emoji.name == "💰":
                    if player_coin == 0 or player_coin < last_count_fee:
                        response = f"It seems {member.mention} doesn't have enough coins! If somebody else wants to pay the fee, please react with 💰 on their failed count message!"
                    else:
                        query_update_player = "UPDATE players SET coins = coins - %s, last_modified_at = current_timestamp WHERE player_id = %s"
                        data_update_player = (last_count_fee, payload.user_id)
                        query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_status = %s, last_count_fee = last_count_fee * 2, total_fee = total_fee + last_count_fee, last_modified_at = current_timestamp WHERE server_id = %s"
                        data_update_count = ("good", payload.guild_id)
                        cursor.execute(query_update_player, data_update_player)
                        conn.commit()
                        cursor.execute(query_update_count, data_update_count)
                        conn.commit()
                        response = f"{member.mention} has decided to pay with their coins! The count resumes! Have fun!"
                        self.bot.logger.info('continue count')
                elif payload.emoji.name == "🔁":
                    query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_modified_at = current_timestamp WHERE server_id = %s"
                    data_update_count = (payload.guild_id,)
                    cursor.execute(query_update_count, data_update_count)
                    conn.commit()
                    response = f"It seems {member.mention} wants to start over!\nReact with 🔁 if you wish you start over \nor, react with 💰 if you wish to continue on their failed count message!\nBut remember, you need to pay the fine of {last_count_fee:,}"
                    self.bot.logger.info('restart count wait')
            else:
                if datetime.datetime.now() >= max_count_game_reaction_time:
                    if payload.emoji.name == "💰":
                        if player_coin == 0 or player_coin < last_count_fee:
                            response = f"Well, it seems {member.mention} also doesn't have enough money! Oh well! The count resets to 0! Have fun!"
                            query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_number = 0, last_count_status = %s, last_count_fee = 300, last_count_multiplier = %s, last_modified_at = current_timestamp WHERE server_id = %s"
                            data_update_count = ("good", last_count_multiplier, payload.guild_id)
                            cursor.execute(query_update_count, data_update_count)
                            conn.commit()
                            self.bot.logger.info('restart count')
                            is_restart = True
                        else:
                            query_update_player = "UPDATE players SET coins = coins - %s, last_modified_at = current_timestamp WHERE player_id = %s"
                            data_update_player = (last_count_fee, payload.user_id)
                            query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_status = %s, last_count_fee = last_count_fee * 2, total_fee = total_fee + last_count_fee, last_modified_at = current_timestamp WHERE server_id = %s"
                            data_update_count = ("good", payload.guild_id)
                            cursor.execute(query_update_player, data_update_player)
                            conn.commit()
                            cursor.execute(query_update_count, data_update_count)
                            conn.commit()
                            response = f"{member.mention} has decided to pay with their coins! The count resumes! Have fun!"
                            self.bot.logger.info('continue count')
                    elif payload.emoji.name == "🔁":
                        response = f"Well, it seems {member.mention} also wants to start over! Oh well! The count resets to 0! Have fun!"
                        query_update_count = "UPDATE count_game SET last_count_member_id = 1, last_count_number = 0, last_count_status = %s, last_count_fee = 300, last_count_multiplier = %s, last_modified_at = current_timestamp WHERE server_id = %s"
                        data_update_count = ("good", last_count_multiplier, payload.guild_id)
                        cursor.execute(query_update_count, data_update_count)
                        conn.commit()
                        self.bot.logger.info('restart count')
                        is_restart = True

            if response is None:
                return
            embed = discord.Embed(title="Chain Counting Game", description=response, color=discord.Color.teal())
            embed.set_thumbnail(url="https://i.imgur.com/DMvoEus.png")
            if last_count_multiplier == 3 and is_restart is True:
                embed.add_field(name="Note", value="The count resets to 0 now with a `x3 multiplier`.\nYou now need to count the multiples of 3 (3, 6, 9, ...)\nGood luck, have fun!")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        conn = self.bot.conn
        cursor = conn.cursor()
        guild_id = message.guild.id
        query_count = "SELECT count_game_channel_id from count_game WHERE server_id = %s"
        data_count = (guild_id,)
        cursor.execute(query_count,data_count)
        result = cursor.fetchall()
        if len(result) > 0:
            count_game_channel_id = result[0][0]
        else:
            count_game_channel_id = None

        if message.channel.id == count_game_channel_id:
            if message.author.bot:
                return

            cursor = conn.cursor()
            query_count = "SELECT last_count_number, last_count_member_id, last_count_status, last_count_fee from count_game where server_id = %s"
            data_count = (message.guild.id, )
            cursor.execute(query_count,data_count)
            result = cursor.fetchall()
            last_count_number = result[0][0]
            last_count_member_id = result[0][1]
            last_count_status = result[0][2]
            last_count_fee = result[0][3]
            try:
                content = int(message.content)
            except:
                content = ""
            if last_count_status != 'good':
                await message.delete()
                return

            if not isinstance(content, int):
                return

            response = None
            if (content != last_count_number + 1) or (message.author.id == last_count_member_id):
                self.bot.logger.info('wrong number or same member')
                failed_count = True
                query = "UPDATE count_game SET last_count_member_id = %s, last_count_message_id = %s, last_count_status = %s, last_count_member_pay = %s, max_count_game_reaction_time = %s, last_modified_at = current_timestamp where server_id = %s"
                data = (message.author.id, message.id, "bad", "wait", datetime.datetime.now() + datetime.timedelta(seconds=15),message.guild.id)
                cursor.execute(query,data)
                conn.commit()
                await message.add_reaction("❌")
                await message.add_reaction("💰")
                await message.add_reaction("🔁")
                response = f"Oh no! {message.author.mention} broke the chain. (**{content}**)!\nYou could react with 💰 to pay a small fine of **{last_count_fee:,}** coins in order to continue the game!\nOr, if you wish to restart, simply react to the 🔁 and start all over again from 1!"
            else:
                await message.add_reaction("✅")
                failed_count = False
                coins = 0
                if content % 1000 == 0:
                    coins = 75000
                    response = f"Teamwork makes the dream work! {message.author.mention}, you just hit **{content}** ! Take this **{int(coins):,}** coins, but don't forget to split the cash!"
                elif content % 500 == 0:
                    coins = 35000
                    response = f"**{content}** ! You guys seem to be working hard! Here's **{int(coins):,}** coins for you, {message.author.mention}, and don't forget to share it to your friends!"
                elif content % 100 == 0:
                    coins = 10000
                    response = f"**{content}** ! Keep it going, {message.author.mention}! Here's **{int(coins):,}** coins for you!"

                query = "UPDATE count_game SET last_count_member_id = %s, last_count_number = %s, last_modified_at = current_timestamp where server_id = %s"
                data = (message.author.id, content, message.guild.id)
                cursor.execute(query,data)
                conn.commit()

                query_coin = "UPDATE players SET coins = coins + %s, last_modified_at = current_timestamp WHERE player_id = %s"
                data_coin = (coins, message.author.id)
                cursor.execute(query_coin, data_coin)
                conn.commit()

            if response is not None:
                embed = discord.Embed(title="Chain Counting Game", description=response, color=discord.Color.teal())
                embed.set_thumbnail(url="https://i.imgur.com/DMvoEus.png")
                if failed_count:
                    embed.add_field(name="Note",value="Only the player, who has broken the chain, can react. If there are no reactions within 15 seconds, it is then open for other players to react with 💰 on their failed count message.")
                await message.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(CountGame(bot))