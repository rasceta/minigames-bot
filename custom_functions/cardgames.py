import random
import discord

def get_random_card_game_name():
    number = random.randint(1,100)
    if number <= 45:
        game = "GTC"
    elif number <= 80:
        game = "PCC"
    elif number <= 100:
        game = "ACE"
    return game

def get_card_game_intro(game_name):
    description = ""
    title = ""
    if game_name == "GTC":
        title = "**Guess the Color**"
        description = '''Want to even the odds? I got a game just for you!

**Guess a color!** It's a 50/50 chance! What's there to lose? You can only bet **2000** amount of coins!
Please enter `!apollo guess [red/black] <bet amount>` to participate! Place your bets everyone! **Place your bets!**

Looking forward to your answers!
'''
        url_img = "https://i.ibb.co/Gt3fQRx/two-back-of-cards.png"
    elif game_name == "PCC":
        title = "**Pick a colored card**"
        description = '''Ohoo! Welcome! This one's a little tricky!
Behold! **Colored Cards!**

Pick a color! Though, I'd be wary though, you have a **1 in 4 chance** of winning! You can only bet **4000** amount of coins!
Please enter `!apollo guess [spade/club/diamond/heart] <bet amount>` to participate! Place your bets everyone! **Place your bets!**

May lady luck be on your side!
'''
        url_img = "https://i.ibb.co/8b0Jfjr/four-back-of-cards.png"
    elif game_name == "ACE":
        title = "**Ace in the hole**"
        description = '''The time has come! **Ace in the hole!**

One of out of these ten cards is an **Ace!** You have a **1 in 10** chance of winning! Be wary of how much you bet! **You can bet up to 500.000 amount of coins!**!
Please enter `!apollo guess [1 to 10] <bet amount>` to participate! Place your bets everyone! **Place your bets!**

May luck be on your side! Have at it!
'''
        url_img = "https://i.ibb.co/P6zd7cs/ten-back-of-cards.png"

    return (title, description, url_img)

def get_card_game_outro(game_name, answer):
    if game_name == "GTC":
        if answer == "black":
            url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-spades-iain-macarthur.jpg"
        elif answer == "red":
            url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-hearts-mr-kone.jpg"
        description = f"Ding ding! It's **{answer}**\nWell, that's about that! Look forward to next time"
        title = "**Guess the Color**"
    elif game_name == "PCC":
        if answer == "spade":
            url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-spades-iain-macarthur.jpg"
        elif answer == "club":
            url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-clubs-andreas-preis.jpg"
        elif answer == "diamond":
            url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-diamonds-jordan-debney.jpg"
        elif answer == "heart":
            url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-hearts-mr-kone.jpg"

        title = "**Pick a Colored Card**"
        description=f"Ding ding! It's **{answer}**!\nWell, that's about that! Look forward to next time."
    elif game_name == "ACE":
        title = "**Ace in the hole**"
        description=f"Ding ding! It's **{answer}**!\nWell, that's about that! Don't worry! There's always next time"
        url_list = ["https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-spades-iain-macarthur.jpg",
                "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-clubs-andreas-preis.jpg",
                "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-diamonds-jordan-debney.jpg",
                "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-hearts-mr-kone.jpg"]
        url_img = random.choice(url_list)

    return(title, description, url_img)

def get_guess_the_color_answer(card,players_won):
    card = card.lower()
    url_img = ""
    if card == "black":
        url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-spades-iain-macarthur.jpg"
    elif card == "red":
        url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-hearts-mr-kone.jpg"
    
    description = f"Ding ding! It's **{card}**!\nWell, that's about that! Look forward to next time"
    return(description, url_img)

def get_colored_card_answer(card,players_won):
    card = card.lower()
    url_img = ""
    if card == "spade":
        url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-spades-iain-macarthur.jpg"
    elif card == "club":
        url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-clubs-andreas-preis.jpg"
    elif card == "diamond":
        url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-diamonds-jordan-debney.jpg"
    elif card == "heart":
        url_img = "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-hearts-mr-kone.jpg"
    
    description=f"Ding ding! It's **{card}**\nWell, that's about that! Look forward to next time."
    return (description, url_img)

def get_ace_in_the_hole_answer(number,players_won):
    description=f"Ding ding! It's **{number}**\nWell, that's about that! Don't worry! There's always next time"
    url_list = ["https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-spades-iain-macarthur.jpg",
                "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-clubs-andreas-preis.jpg",
                "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-diamonds-jordan-debney.jpg",
                "https://s3.amazonaws.com/img.playingarts.com/one-small-hd/ace-of-hearts-mr-kone.jpg"]
    
    return (description, random.choice(url_list))