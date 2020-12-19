import discord
import random
import datetime
import psycopg2
import asyncio
import logging
import util
import queries

from discord.ext import commands, tasks

class Minigames(commands.Bot):
    def __init__(self, command_prefix: str, conn):
        super().__init__(command_prefix, case_insensitive=True)

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s|%(name)s::%(levelname)s: %(message)s'))
        self.logger = logging.getLogger('MinigamesBot')
        self.logger.addHandler(handler)
        self.logger.setLevel('INFO')
        self.remove_command('help')

        self.conn = conn

    async def on_ready(self):
        queries.create_tables(self.conn)
        self.logger.info(f"Minigames Bot is Ready! (Prefix: {self.command_prefix})")
        self.logger.info("Database created and Successfully Connected to PostgreSQL")

    async def on_guild_join(self, guild):
        cursor = self.conn.cursor()
        query = "INSERT INTO servers(server_id,server_name,created_at,last_modified_at) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING"
        data = (guild.id, guild.name, datetime.datetime.now(), datetime.datetime.now()) 
        cursor.execute(query,data)
        self.conn.commit()

    async def on_guild_remove(self, guild):
        cursor = self.conn.cursor()
        query_server = "DELETE FROM servers WHERE server_id = %s"
        query_count = "DELETE FROM count_game WHERE server_id = %s"
        data = (guild.id, ) 
        cursor.execute(query_server,data)
        self.conn.commit()
        cursor.execute(query_count,data)
        self.conn.commit()

    async def on_raw_reaction_add(self, payload):
        user_id = payload.user_id
        message_id = payload.message_id
        guild_id = payload.guild_id
        member = payload.member

        cursor = self.conn.cursor()
        self.conn.commit()
        query = "SELECT free_coins_message_id, free_coins_reaction_time, free_coins_amount from servers WHERE server_id = %s"
        data = (guild_id,)
        cursor.execute(query,data)
        result = cursor.fetchall()
        free_coins_message_id = result[0][0]
        max_reaction_time = result[0][1]
        free_coins_amount = result[0][2]

        if (message_id == free_coins_message_id) and (not member.bot) and (payload.emoji.name == '💰'):
            if datetime.datetime.now() <= max_reaction_time:
                query = "UPDATE players SET coins = coins + %s WHERE player_id = %s"
                data = (free_coins_amount,user_id)
                cursor.execute(query,data)
                self.conn.commit()

    async def on_raw_reaction_remove(self, payload):
        user_id = payload.user_id
        message_id = payload.message_id
        guild_id = payload.guild_id
        guild = self.get_guild(guild_id)
        member = await guild.fetch_member(user_id)

        cursor = self.conn.cursor()
        query = "SELECT free_coins_message_id, free_coins_reaction_time, free_coins_amount from servers WHERE server_id = %s"
        data = (guild_id,)
        cursor.execute(query,data)
        result = cursor.fetchall()
        free_coins_message_id = result[0][0]
        max_reaction_time = result[0][1]
        free_coins_amount = result[0][2]

        if (message_id == free_coins_message_id) and (not member.bot) and (payload.emoji.name == '💰'):
            if datetime.datetime.now() <= max_reaction_time:
                query = "UPDATE players SET coins = coins - %s WHERE player_id = %s"
                data = (free_coins_amount,user_id)
                cursor.execute(query,data)
                self.conn.commit()

    async def on_message(self, message):
        if message.author.bot:
            return

        player = message.author
        cursor = self.conn.cursor()

        query = "INSERT INTO players (player_id, player_name, coins, register_date, " \
            "next_daily_coins_time, next_weekly_coins_time, created_at, last_modified_at) " \
            "VALUES (%s,%s,%s,current_timestamp,current_timestamp,current_timestamp,current_timestamp,current_timestamp)" \
            "ON CONFLICT DO NOTHING"
        data = (player.id, player.name, 1000)
        cursor.execute(query,data)
        self.conn.commit()

        await self.process_commands(message)