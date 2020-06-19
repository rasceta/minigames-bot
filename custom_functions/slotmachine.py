import random
import discord

def get_slot():
    slot = []
    for i in range(0,4):
        slot.append(random.choice(['⭐','🌍','🌑','☀']))
    return slot
