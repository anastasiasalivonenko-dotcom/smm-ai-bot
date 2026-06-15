import os
import telebot
import requests
import threading
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Инициализируем ключи из настроек сервера
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
# Вместо OpenAI используем тот же слот для ключа Gemini
GEMINI_API_KEY = os.environ.get('OPENAI_API_KEY')
SERPER_API_KEY = os.environ.get('SERPER_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def search_google(query):
    """Ищет топ-3 ссылки в Google через Serper API"""
    url = "https://google.serper.dev/search"
    payload = {"q": f"{query} instagram сайт"}
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        results = response.json().get('organic', [])
        return [f"{res.get('title')}: {res.get('link')}" for res in results[:3]]
    except Exception:
        return []


    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_json = response.json()
        text_output = res_json['candidates'][0]['content']['parts'][0]['text']
        return text_output
    except Exception as e:
        return f"Ошибка ИИ Gemini: {str(e)}"
def analyze_and_create_offer(company_info):
    """Генерирует SMM-оффер через бесплатный Google Gemini API с обходом фильтров"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    prompt = (
        f"Ты — дружелюбный SMM-консультант. Посмотри на эту компанию: {company_info}. "
        f"Напиши короткое, вдохновляющее предложение для их Instagram (на 3-4 абзаца). "
        f"Предложи улучшить оформление профиля, добавить регулярные Reels и выстроить воронку в сторис. "
        f"Пиши вежливо, используй эмодзи и структурируй текст, чтобы его было приятно читать."
    )
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_json = response.json()
        
        # Проверяем, заблокировал ли Google ответ
        if 'candidates' in res_json and res_json['candidates'][0].get('finishReason') == 'SAFETY':
            return "⚠️ ИИ заблокировал генерацию из-за фильтров безопасности Google. Попробуй другой запрос."
            
        text_output = res_json['candidates'][0]['content']['parts'][0]['text']
        return text_output
    except Exception as e:
        # Если API выдает ошибку структуры, выведем дебаг-инфо для понимания
        return f"Не удалось сгенерировать оффер. Ответ от Google: {str(res_json.get('error', e))}"
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой автономный SMM-скаут. Напиши мне нишу и город через запятую (например: `Салоны красоты, Киев`), и я найду компании и составлю для них крутые офферы! 🚀")

@bot.message_handler(func=lambda message: True)
def handle_search(message):
    if ',' not in message.text:
        bot.reply_to(message, "Пожалуйста, отправь запрос через запятую. Пример: `Салоны красоты, Киев`")
        return

    bot.reply_to(message, "Понял задачу! Запускаю скаутов, ищу компании в Google и соцсетях... 🔍")
    companies = search_google(message.text)

    if not companies:
        bot.reply_to(message, "Не удалось найти компании по этому запросу. Попробуй изменить формулировку.")
        return

    for company in companies:
        bot.send_message(message.chat.id, f"🏢 **Найдена компания:**\n{company}\n\n🤖 *ИИ анализирует бренд и составляет оффер...*")
        offer = analyze_and_create_offer(company)
        bot.send_message(message.chat.id, f"📝 **Готовое предложение для отправки:**\n\n{offer}")

def run_dummy_server():
    server_address = ('', int(os.environ.get('PORT', 8000)))
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    httpd.serve_forever()

# Запускаем пустышку-сервер для обхода проверки портов Render
threading.Thread(target=run_dummy_server, daemon=True).start()

if __name__ == "__main__":
    bot.infinity_polling()
