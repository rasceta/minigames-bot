import psycopg2
import os
import discord
import datetime
from dotenv import load_dotenv

load_dotenv()
def create_tables(conn):
	query_players = '''
	CREATE TABLE IF NOT EXISTS public.players (
		player_id BIGINT PRIMARY KEY,
		player_name TEXT NOT NULL,
		register_date TIMESTAMP,
		coins INTEGER NOT NULL,
		next_daily_coins_time TIMESTAMP,
		next_weekly_coins_time TIMESTAMP,
		created_at TIMESTAMP,
		last_modified_at TIMESTAMP
	);
    '''
	query_items = '''
	CREATE TABLE IF NOT EXISTS public.items (
		id SERIAL PRIMARY KEY,
		player_id BIGINT NOT NULL,
		player_name TEXT NOT NULL,
		item_name TEXT NOT NULL,
		item_code TEXT NOT NULL,
		created_at TIMESTAMP,
		last_modified_at TIMESTAMP
	);
    '''
	query_servers = '''
	CREATE TABLE IF NOT EXISTS public.servers (
		server_id BIGINT PRIMARY KEY,
		server_name TEXT NOT NULL,
		count_game_channel_id BIGINT,
		free_coins_channel_id BIGINT,
		free_coins_amount INT,
		free_coins_message_id BIGINT,
		free_coins_reaction_time TIMESTAMP,
		created_at TIMESTAMP,
		last_modified_at TIMESTAMP
	);
	'''
	query_count = '''
	CREATE TABLE IF NOT EXISTS public.count_game (
		server_id BIGINT PRIMARY KEY,
		count_game_channel_id BIGINT,
		last_count_number INT,
		last_count_member_id BIGINT,
		last_count_message_id BIGINT,
		last_count_status TEXT,
		last_count_fee INT,
		last_count_multiplier INT,
		last_count_member_pay TEXT,
		max_count_game_reaction_time TIMESTAMP,
		total_fee INT,
		created_at TIMESTAMP,
		last_modified_at TIMESTAMP
	);
	'''

	cursor = conn.cursor()
	cursor.execute(query_players)
	cursor.execute(query_items)
	cursor.execute(query_servers)
	cursor.execute(query_count)
	conn.commit()