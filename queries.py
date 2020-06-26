import psycopg2
import os
import discord
import datetime
from dotenv import load_dotenv

load_dotenv()
async def create_tables():

    conn = psycopg2.connect(user=os.getenv("DATABASE_USERNAME"),
                            password=os.getenv("DATABASE_PASSWORD"),
                            host=os.getenv("DATABASE_HOST"),
                            port=os.getenv("DATABASE_PORT"),
                            database=os.getenv("DATABASE_DB"))
    query_players = '''
CREATE TABLE IF NOT EXISTS public.players (
	player_id BIGINT PRIMARY KEY,
	player_name TEXT NOT NULL,
	register_date TIMESTAMP,
	coins INTEGER NOT NULL,
	last_card_game_answer TEXT,
	last_card_game_bet INTEGER,
	last_card_game_answer_time TIMESTAMP,
	next_slot_time TIMESTAMP,
	next_donate_time TIMESTAMP,
	next_donation_time TIMESTAMP,
	next_daily_coins_time TIMESTAMP,
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
	created_at TIMESTAMP,
	last_modified_at TIMESTAMP
);
    '''
    query_servers = '''
CREATE TABLE IF NOT EXISTS public.servers (
	server_id BIGINT PRIMARY KEY,
	server_name TEXT NOT NULL,
	card_game_channel_id BIGINT,
	slot_game_channel_id BIGINT,
	count_game_channel_id BIGINT,
	exchange_channel_id BIGINT,
	free_coins_channel_id BIGINT,
	bot_channel_id BIGINT,
	free_coins_amount INT,
	last_free_coins_message_id BIGINT,
	max_free_coins_reaction_time TIMESTAMP,
	last_card_games_name TEXT,
	last_card_games_answer TEXT,
	last_card_games_message_id BIGINT,
	max_card_games_reaction_time TIMESTAMP,
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
	last_count_member_pay TEXT,
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
    conn.close()
    print(f"Database created and Successfully Connected to PostgreSQL")