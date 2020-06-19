import random
import discord

def get_slot():
    slot = []
    for i in range(0,4):
        number = random.randint(1,100)
        if number <= 40:
            slot.append('⭐')
        elif number <= 60:
            slot.append('🌑')
        elif number <= 80:
            slot.append('🌍')
        else:
            slot.append('☀')
    return slot
