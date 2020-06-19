import psycopg2
import json
import discord
import datetime

async def create_tables():
    with open('connection.json') as f:
        data = json.load(f)
    conn = psycopg2.connect(user=data["user"],
                            password=data["password"],
                            host=data["host"],
                            port=data["port"],
                            database=data["database"])
    cursor = conn.cursor()

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
    cursor.execute(query_players)
    cursor.execute(query_items)
    cursor.execute(query_servers)
    conn.commit()
    print(f"Database created and Successfully Connected to PostgreSQL")