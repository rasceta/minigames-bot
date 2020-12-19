import discord
import asyncio
import random
import datetime
import util

from discord.ext import commands, tasks

class BackgroundTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(minutes=10)
    async def free_coins(self):
        conn = self.bot.conn
        cursor = conn.cursor()
        query = "SELECT free_coins_channel_id from servers"
        cursor.execute(query)
        result = cursor.fetchall()
        free_coins_channel_id_list = [e[0] for e in result]

        img_url = "https://i.imgur.com/egt7kT0.png"
        free_coins_amount = 50

        for channel_id in free_coins_channel_id_list:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue
            embed = discord.Embed(title="Free Coins",
                                description=f"Hello, hello! The mysterious coin creature's here. It has returned for all to see! It's here to give you all free coins! Yes! You heard that right! Free coins!",
                                color=discord.Color.dark_gold())
            embed.set_thumbnail(url=img_url)
            embed.set_footer(text="React with 💰 quickly!")
            new_message = await channel.send(embed=embed)
            await new_message.add_reaction("💰")
            max_reaction_time = datetime.datetime.now() + datetime.timedelta(seconds=30)

            query = "UPDATE servers SET last_free_coins_message_id = %s, max_free_coins_reaction_time = %s, free_coins_amount = %s WHERE free_coins_channel_id = %s"
            data = (new_message.id, max_reaction_time, free_coins_amount, channel.id)
            cursor.execute(query,data)
            conn.commit()

        await asyncio.sleep(30)

        cursor = conn.cursor()
        query = "SELECT free_coins_channel_id, last_free_coins_message_id from servers"
        cursor.execute(query)
        result_list = cursor.fetchall()
        free_coins_channel_id_list = [e[0] for e in result_list]
        free_coins_message_id_list = [e[1] for e in result_list]

        new_embed = discord.Embed(title="Free Coins",
                            description="I must go now! I'll be back whenever!")
        new_embed.set_thumbnail(url="https://i.imgur.com/egt7kT0.png")

        for idx, channel_id in enumerate(free_coins_channel_id_list):
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue
            message_id = free_coins_message_id_list[idx]
            message = await channel.fetch_message(message_id)
            if channel is not None:
                await message.edit(embed=new_embed)

    @free_coins.before_loop
    async def free_coins_before(self):
        await self.bot.wait_until_ready()

    @commands.command(name='start')
    async def start(self, ctx, task_name:str=None):
        if ctx.author.guild_permissions.administrator:
            task_list = ["freecoins"]
            if task_name is None:
                return

            if task_name in task_list:
                if task_name == "freecoins":
                    self.free_coins.start()
                embed = util.log_embed(f"{task_name} task has been started", "success")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"There's only {' and '.join(task_list)} task")
            await ctx.message.delete()

    @commands.command(name='stop')
    async def stop(self, ctx, task_name:str=None):
        if ctx.author.guild_permissions.administrator:
            task_list = ["freecoins"]
            if task_name is None:
                return

            if task_name in task_list:
                if task_name == "freecoins":
                    self.free_coins.stop()
                embed = util.log_embed(f"{task_name} task has been stopped", "success")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"There's only {' and '.join(task_list)} task")
            await ctx.message.delete()

def setup(bot):
    bot.add_cog(BackgroundTasks(bot))