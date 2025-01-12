import numpy as np
import pandas as pd
from scipy.io.wavfile import write
import telebot
import random
import os
import time

# Used this notebook for inspiration - 
# https://github.com/tudev/Workshops-2020-2021/blob/master/Python%20YouTube%20Tutorials/Python_Reading%2C_Writting_and_Playing_Audio_Files!/Python_Reading%2C_Writting_and_Playing_Audio_Files!_(FULL).ipynb

# Constants and initializations 
SAMPLE_RATE = 44100
GAME_LENGTH_IN_SECONDS = 60
C_FILE_NAME = 'c4.mp3'

botToken = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(token=botToken)

df = pd.read_excel('./note_frequencies.xlsx')
octave = df['Note'].to_list()
freq = df['Frequency (Hz)'].to_list()
note_freqs = {note:sound for note,sound in zip(octave,freq)}
correct_notes_per_chat_id = dict()
note_freqs[''] = 0.0

list_of_notes = ["C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4"]

dictionary_of_notes = {
    "CB": "B",
    "DB": "C#",
    "EB": "D#",
    "FB": "E",
    "GB": "F#",
    "AB": "G#",
    "BB": "A#",
    "E#": "F",
    "B#": "C"
}

fileType = "mp3"
running_games = dict()
scores = dict()

def getNote(note):
    if (f"{note}4" in list_of_notes):
        return f"{note}4"
    return f"{dictionary_of_notes[note]}4"

def isLegalNote(note):
    note_to_test = note.upper()
    if (f"{note_to_test}4" in list_of_notes):
        return True
    if (note_to_test in dictionary_of_notes):
        return True
    return False

def get_wave(freq, duration=0.5):
    amplitude = 4096
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    wave = amplitude * np.sin(2 * np.pi * freq * t)
    
    return wave

def get_song_data(music_notes):
    song = [get_wave(note_freqs[note]) for note in music_notes.split('-')]
    song = np.concatenate(song)
    song = song * (16300/np.max(song))
    return song

# Sends the user a c note
@bot.message_handler(commands=['givemec'])
def givemec(message):
    chat_id = message.chat.id
    bot.send_voice(chat_id=chat_id, voice=open(C_FILE_NAME, 'rb'))

# sends the user a random note (not as part of a one minute game)
@bot.message_handler(commands=['hitme'])
def hitme(message):
    chat_id = message.chat.id
    if (chat_id in running_games and running_games[chat_id] == True):
        bot.send_message(chat_id=chat_id, text="You are playing a game, cannot do /hitme")
        return
    
    file_name = f'music_for_user_{chat_id}.{fileType}'
    send_random_note_to_user(chat_id=chat_id, file_name=file_name)
    time.sleep(1)
    os.remove(file_name)

# Starts a one minute game (counts how many notes the user managed to identify)
@bot.message_handler(commands=['startagame'])
def start_a_game(message):

    chat_id = message.chat.id
    if (chat_id in running_games and running_games[chat_id] == True):
        bot.send_message(chat_id=chat_id, text="You are already playing a game...")
        return
    running_games[chat_id] = True

    bot.send_message(chat_id=chat_id, text="You will have 1 minute to try to get as many as possible.")
    time.sleep(1)
    bot.send_message(chat_id=chat_id, text="Remember, this is a C note:")
    bot.send_voice(chat_id=chat_id, voice=open(C_FILE_NAME, 'rb'))
    time.sleep(1)
    bot.send_message(chat_id=chat_id, text="Ready?")
    time.sleep(1)
    bot.send_message(chat_id=chat_id, text="Set!")
    time.sleep(1)
    bot.send_message(chat_id=chat_id, text="Go!!!")

    scores[chat_id] = 0

    file_name = f'music_for_user_{chat_id}.{fileType}'
    send_random_note_to_user(chat_id, file_name=file_name)

    # Wait a minute before we end the game and report on the score
    time.sleep(GAME_LENGTH_IN_SECONDS)
    bot.send_message(chat_id=chat_id, text=f"GAME OVER. Score: {scores[chat_id]}")
    running_games[chat_id] = False
    scores[chat_id] = 0
    del correct_notes_per_chat_id[chat_id]
    os.remove(file_name)

# Handles messages from user during a game
@bot.message_handler(func=lambda message: isLegalNote(message.text.upper()) and message.chat.id in running_games and running_games[message.chat.id] == True, content_types=['text'])
def handle_guess_during_game(message):
    chat_id = message.chat.id
    note_from_user = getNote(message.text.upper())
    correct_answer = correct_notes_per_chat_id[chat_id]

    if(note_from_user == correct_answer):
        bot.send_message(chat_id=chat_id, text="Nice!!!")
        scores[chat_id] = scores[chat_id]+1
        file_name = f'music_for_user_{chat_id}.{fileType}'
        send_random_note_to_user(chat_id, file_name=file_name)
    else:
        bot.send_message(chat_id=chat_id, text="Nope")

def send_random_note_to_user(chat_id, file_name):
    # Select a random note
    random_music_note = random.choice(list_of_notes)
    note_values_as_array = get_song_data(random_music_note)

    # Save correct answer for this user
    correct_notes_per_chat_id[chat_id] = random_music_note

    # Create an audio file to send to the user
    write(file_name, SAMPLE_RATE, note_values_as_array.astype(np.int16))
    bot.send_voice(chat_id=chat_id, voice=open(file_name, 'rb'))

# Handles all messages for which the lambda returns True
@bot.message_handler(func=lambda message: isLegalNote(message.text.upper()), content_types=['text'])
def handle_guess_regular(message):
    chat_id = message.chat.id
    note_from_user = getNote(message.text.upper())
    if (chat_id not in correct_notes_per_chat_id):
        bot.send_message(chat_id=chat_id, text="No music yet, please send /hitme for a single note or /startagame to start playing.")
        return
    else:
        correct_answer = correct_notes_per_chat_id[chat_id]
        if(note_from_user == correct_answer):
            bot.send_message(chat_id=chat_id, text="Nice!!!")
        else:
            bot.send_message(chat_id=chat_id, text="Nope")


@bot.message_handler(commands=['version'])
def getAppVersion(message):
    chat_id = message.chat.id
    bot.send_message(chat_id=chat_id, text="App version: 12")
    return

# Welcome message to user
@bot.message_handler(content_types=['text'])
def send_welcome(message):
    
    chat_id = message.chat.id
    if (chat_id not in correct_notes_per_chat_id):
        # User did not click hitme yet
        bot.send_message(chat_id=chat_id, text=f"To start, please select /givemec or /hitme (for one practice note) or /startagame (to start a one minute game)")
        return
    else:
        # We have a note waiting
        bot.send_message(chat_id=chat_id, text=f"To guess, please send any of the following: {[a[:-1] for a in list_of_notes]} or the equivalent Bemol")

# Catch-all handler
@bot.message_handler(content_types=['audio', 'photo', 'voice', 'video', 'document', 'location', 'contact', 'sticker'])
def default_message(message):
    chat_id = message.chat.id
    bot.send_message(chat_id=chat_id, text=f"Only text messages are supported with this bot.")

bot.infinity_polling()