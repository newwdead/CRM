#!/bin/bash

# Script to obtain SSL certificates for ibbase.ru domains
# Run this after DNS records are configured

set -e

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║         🔒 Получение SSL Сертификатов для ibbase.ru 🔒                   ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check DNS
echo "🔍 Проверяю DNS записи..."
echo ""

dns_ok=0
for domain in ibbase.ru api.ibbase.ru monitoring.ibbase.ru; do
    result=$(host $domain 2>&1 | grep "95.163.183.25" || true)
    if [ -n "$result" ]; then
        echo "✅ $domain → 95.163.183.25"
        dns_ok=$((dns_ok+1))
    else
        echo "❌ $domain → НЕ НАСТРОЕН"
    fi
done

echo ""
echo "Настроено доменов: $dns_ok из 3"
echo ""

if [ $dns_ok -lt 3 ]; then
    echo "⚠️  ВНИМАНИЕ: Не все DNS записи настроены!"
    echo ""
    echo "Пожалуйста, добавьте следующие A-записи в панели управления доменом:"
    echo ""
    echo "  @ или ibbase.ru         → 95.163.183.25"
    echo "  www                     → 95.163.183.25"
    echo "  api                     → 95.163.183.25"
    echo "  monitoring              → 95.163.183.25"
    echo ""
    read -p "DNS записи настроены? Продолжить? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Отменено. Запустите скрипт снова после настройки DNS."
        exit 1
    fi
fi

echo ""
echo "📜 Получаю SSL сертификаты от Let's Encrypt..."
echo ""

# Get certificates
sudo certbot --nginx \
    -d ibbase.ru \
    -d www.ibbase.ru \
    -d api.ibbase.ru \
    -d monitoring.ibbase.ru \
    --non-interactive \
    --agree-tos \
    --email admin@ibbase.ru \
    --redirect

echo ""
echo "✅ SSL сертификаты получены успешно!"
echo ""
echo "🔄 Перезапускаю Nginx..."
sudo systemctl reload nginx

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ГОТОВО! Ваши сайты теперь доступны по HTTPS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 https://ibbase.ru              → Frontend"
echo "  🌐 https://www.ibbase.ru          → Frontend (с www)"
echo "  🔌 https://api.ibbase.ru          → Backend API"
echo "  📊 https://monitoring.ibbase.ru   → Grafana"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Автообновление сертификатов настроено автоматически (certbot.timer)"
echo "    Проверка дважды в день, обновление за 30 дней до истечения"
echo ""

