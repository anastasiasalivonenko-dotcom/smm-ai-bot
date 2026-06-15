```python
import os
import telebot
import requests
from openai import OpenAI

# Инициализируем ключи из настроек сервера
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
SERPER_API_KEY = os.environ.get('SERPER_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

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

def analyze_and_create_offer(business_info):
    """Генерирует индивидуальное предложение через OpenAI"""
    prompt = f"""
    Ты — опытный SMM-стратег и эксперт по конкурентному анализу брендов. 
    Твоя задача — проанализировать компанию по предоставленной ссылке и названию: {business_info}.
    
    Напиши точечный, персонализированный оффер для этой компании по улучшению их SMM (Reels, сторис, воронки продаж). 
    Предложение должно быть коротким, цепляющим, профессиональным и бить в боли конкретной ниши. Избегай банального спама.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка анализа ИИ: {str(e)}"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет, Анастасия! Я твой автономный SMM-скаут. 🚀\nОтправь мне нишу и город в формате: `Шоурумы, Киев` или `Зоотовары, Одесса`, и я найду клиентов.")

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
        bot.send_message(message.chat.id, f"🏬 **Найдена компания:**\n{company}\n\n🤖 *ИИ анализирует бренд и составляет оффер...*")
        offer = analyze_and_create_offer(company)
        bot.send_message(message.chat.id, f"📝 **Готовое предложение для отправки:**\n\n{offer}")

if __name__ == "__main__":
    bot.infinity_polling()
