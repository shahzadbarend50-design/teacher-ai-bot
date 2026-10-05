import os
import asyncio
import telebot
import google.generativeai as genai
import edge_tts
import PIL.Image

# 1. API Keys
TELEGRAM_BOT_TOKEN = "8678060536:AAEvef3r5yuiocFAD2DM6OX4PZ38ut_yN4s"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"  # یہاں اپنی Gemini API Key لگائیں

# 2. Setup Gemini Model
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# 3. Setup Telegram Bot
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# اردو وائس (Edge TTS) بنانے کا فنکشن
async def text_to_voice(text, output_file):
    communicate = edge_tts.Communicate(text, "ur-PK-UzmaNeural")
    await communicate.save(output_file)

# Start Command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = "السلام علیکم! میں آپ کا AI استاد ہوں۔ مجھے کوئی بھی سوال یا تصویر بھیجیں، میں آپ کو اردو میں قدم بہ قدم حل اور آواز کے ساتھ جواب دوں گا۔"
    bot.reply_to(message, welcome_text)

# Handle Image Messages (تصویر کا جواب)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        status_msg = bot.reply_to(message, "جواب تیار کیا جا رہا ہے، برائے مہربانی چند سیکنڈ انتظار کریں...")
        
        # Download image
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        photo_path = "temp_image.jpg"
        with open(photo_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        img = PIL.Image.open(photo_path)
        
        # Gemini Prompt
        prompt = "آپ ایک ماہر استاد ہیں۔ اس تصویر میں دیے گئے سوال یا مواد کا قدم بہ قدم آسان اردو میں تفصیلی حل فراہم کریں۔"
        response = model.generate_content([prompt, img])
        text_response = response.text
        
        # Send Text Reply
        bot.reply_to(message, text_response)
        
        # Convert Text to Voice (First 800 characters)
        audio_path = "response_voice.mp3"
        asyncio.run(text_to_voice(text_response[:800], audio_path))
        
        # Send Voice Reply
        with open(audio_path, 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
            
        # Clean Temp Files
        if os.path.exists(photo_path):
            os.remove(photo_path)
        if os.path.exists(audio_path):
            os.remove(audio_path)

    except Exception as e:
        bot.reply_to(message, f"معذرت! ایک خرابی پیش آ گئی ہے: {str(e)}")

# Handle Text Messages (تحریری سوال کا جواب)
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        status_msg = bot.reply_to(message, "سوچ رہا ہوں...")
        
        prompt = f"آپ ایک ماہر استاد ہیں۔ اس سوال کا قدم بہ قدم اردو میں جواب دیں: {message.text}"
        response = model.generate_content(prompt)
        text_response = response.text
        
        # Send Text Reply
        bot.reply_to(message, text_response)
        
        # Convert Text to Voice
        audio_path = "response_voice.mp3"
        asyncio.run(text_to_voice(text_response[:800], audio_path))
        
        # Send Voice Reply
        with open(audio_path, 'rb') as audio:
            bot.send_voice(message.chat.id, audio)
            
        if os.path.exists(audio_path):
            os.remove(audio_path)

    except Exception as e:
        bot.reply_to(message, f"معذرت! ایک خرابی پیش آ گئی ہے: {str(e)}")

print("Bot is successfully running...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)