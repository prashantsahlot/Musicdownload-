import telebot
from telebot import types
from pytube import YouTube
import os
import threading
import time
import requests

# Telegram bot token
TOKEN = '7491288128:AAGOA3LVqV9MjI5KALfCwnEZa5ZLDOwW-lc'

# YouTube Data API key
YOUTUBE_API_KEY = 'AIzaSyATjDFifmrmn5vwTRLVcLtNM3q_9_kJ6yk'

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Start image link
START_IMAGE_LINK = 'https://telegra.ph/file/82e3f9434e48d348fa223.jpg'
# Start menu text
START_MENU_TEXT = (
    "Hello there! I'm a song downloading bot with the following commands:\n\n"
    "🔍 Use /search to download youtube video or song \n"
    "   For example, send:\n"
    "   /search royalty"
)

@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot.send_photo(message.chat.id, START_IMAGE_LINK, caption=START_MENU_TEXT)

@bot.message_handler(commands=['search'])
def search(message):
    try:
        query = message.text.split(' ', 1)[1]
        search_results = search_youtube(query)
        if search_results:
            keyboard = types.InlineKeyboardMarkup()
            audio_button = types.InlineKeyboardButton(text="Download Audio", callback_data=f"audio {search_results}")
            video_button = types.InlineKeyboardButton(text="Download Video", callback_data=f"video {search_results}")
            keyboard.add(audio_button, video_button)
            bot.send_message(message.chat.id, "Choose download format:", reply_markup=keyboard)
        else:
            bot.reply_to(message, "No results found.")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

def search_youtube(query):
    try:
        url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&part=snippet&type=video&q={query}"
        response = requests.get(url)
        data = response.json()
        if 'items' in data and len(data['items']) > 0:
            video_id = data['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            return None
    except Exception as e:
        print(f"Error searching for YouTube video: {e}")
        return None

# Define the download_audio function
def download_audio(message, data):
    try:
        handle_download(message, data, is_audio=True)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Define the download_video function
def download_video(message, data):
    try:
        handle_download(message, data, is_audio=False)
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        command, data = call.data.split(' ', 1)
        if command == "audio":
            download_audio(call.message, data)
        elif command == "video":
            download_video(call.message, data)
    except Exception as e:
        print(f"Error handling callback query: {e}")

def handle_download(message, youtube_link, is_audio):
    # Send "downloading" message
    downloading_message = bot.send_message(message.chat.id, "Downloading 0%.")

    # Download the YouTube video
    try:
        yt = YouTube(youtube_link, on_progress_callback=lambda stream, chunk, bytes_remaining: progress_callback(stream, chunk, bytes_remaining, downloading_message))

        # Get the appropriate stream based on user's choice
        if is_audio:
            stream = yt.streams.filter(only_audio=True).first()
            file_type = 'audio'
        else:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            file_type = 'video'

        if not stream:
            bot.edit_message_text("No suitable stream found.", message.chat.id, downloading_message.message_id)
            return

        # Download the media
        file_path = stream.download(filename=f'download.{file_type}')

        # Send the media file to the user if it exists
        if os.path.exists(file_path):
            # Send "uploading" message
            uploading_message = bot.send_message(message.chat.id, "Uploading 67%.")

            media_file = open(file_path, 'rb')
            if is_audio:
                bot.send_audio(message.chat.id, media_file, reply_to_message_id=downloading_message.message_id)
            else:
                bot.send_video(message.chat.id, media_file, reply_to_message_id=downloading_message.message_id)
            media_file.close()

            # Delete the downloaded file
            os.remove(file_path)

            bot.delete_message(message.chat.id, uploading_message.message_id)

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")
        print(f"Error handling download: {e}")
        bot.delete_message(message.chat.id, downloading_message.message_id)

def progress_callback(stream, chunk, bytes_remaining, downloading_message):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percent = int(bytes_downloaded / total_size * 100)
    bot.edit_message_text(f"Downloading {percent}%.", chat_id=downloading_message.chat.id, message_id=downloading_message.message_id)

# Start the bot
bot.polling()
