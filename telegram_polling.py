#!/usr/bin/env python3
"""
Telegram Polling Script for BizCard CRM
Получает обновления от Telegram и отправляет в локальный webhook
"""
import requests
import time
import sys
import os

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8424260030:AAEjZnx2zFQ4KvtP7SjnaHVxlL_1Qw9Pm5s")
WEBHOOK_URL = "http://localhost:8000/telegram/webhook"
POLL_INTERVAL = 1  # секунды между запросами

def get_updates(offset=None):
    """Получить обновления от Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 30, "allowed_updates": ["message", "edited_message"]}
    if offset:
        params["offset"] = offset
    
    try:
        response = requests.get(url, params=params, timeout=35)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка при получении обновлений: {e}")
        return None

def send_to_webhook(update):
    """Отправить обновление в локальный webhook"""
    try:
        response = requests.post(WEBHOOK_URL, json=update, timeout=60)
        return response.status_code, response.json()
    except Exception as e:
        print(f"❌ Ошибка при отправке в webhook: {e}")
        return None, str(e)

def main():
    print("🤖 Telegram Polling для BizCard CRM")
    print(f"📡 Получение обновлений каждые {POLL_INTERVAL}с...")
    print(f"🔗 Webhook: {WEBHOOK_URL}")
    print("=" * 60)
    
    offset = None
    processed_count = 0
    
    while True:
        try:
            # Получить обновления
            result = get_updates(offset)
            
            if not result or not result.get("ok"):
                print(f"⚠️  Не удалось получить обновления: {result}")
                time.sleep(POLL_INTERVAL)
                continue
            
            updates = result.get("result", [])
            
            if not updates:
                print(".", end="", flush=True)
                time.sleep(POLL_INTERVAL)
                continue
            
            print()  # новая строка после точек
            
            # Обработать каждое обновление
            for update in updates:
                update_id = update.get("update_id")
                message = update.get("message") or update.get("edited_message")
                
                if message:
                    chat_id = message.get("chat", {}).get("id")
                    has_photo = "photo" in message
                    text = message.get("text", "")[:50]
                    
                    print(f"📨 Update #{update_id} | Chat: {chat_id} | Photo: {has_photo} | Text: {text}")
                    
                    # Отправить в webhook
                    status, response = send_to_webhook(update)
                    
                    if status == 200:
                        if response.get("created_id"):
                            print(f"   ✅ Контакт создан: ID {response['created_id']}")
                            processed_count += 1
                        elif response.get("ignored"):
                            print(f"   ⏭️  Пропущено: {response['ignored']}")
                        else:
                            print(f"   ✅ Обработано: {response}")
                    else:
                        print(f"   ❌ Ошибка {status}: {response}")
                
                # Обновить offset для следующего запроса
                offset = update_id + 1
            
            print(f"📊 Всего обработано фото: {processed_count}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 Остановка polling...")
            print(f"📊 Всего обработано: {processed_count} фото")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Непредвиденная ошибка: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()

