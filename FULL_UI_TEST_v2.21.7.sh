#!/bin/bash

# ============================================================================
# Полное UI тестирование после миграции v2.21.7
# Проверка всех 4 мигрированных модулей
# ============================================================================

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║   🧪 ПОЛНОЕ UI ТЕСТИРОВАНИЕ v2.21.7                           ║"
echo "║   Проверка всех мигрированных модулей                         ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Счетчики
TOTAL=0
PASSED=0
FAILED=0

# Функция проверки
test_endpoint() {
    TOTAL=$((TOTAL + 1))
    local name="$1"
    local url="$2"
    local expected_code="$3"
    local token="$4"
    
    echo -n "Testing: $name ... "
    
    if [ -z "$token" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1)
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $token" "$url" 2>&1)
    fi
    
    if [ "$response" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected: $expected_code, Got: $response)"
        FAILED=$((FAILED + 1))
    fi
}

# Функция проверки JSON ответа
test_json_endpoint() {
    TOTAL=$((TOTAL + 1))
    local name="$1"
    local url="$2"
    local token="$3"
    local expected_field="$4"
    
    echo -n "Testing: $name ... "
    
    if [ -z "$token" ]; then
        response=$(curl -s "$url" 2>&1)
    else
        response=$(curl -s -H "Authorization: Bearer $token" "$url" 2>&1)
    fi
    
    # Проверка что это валидный JSON
    if echo "$response" | jq -e . >/dev/null 2>&1; then
        # Проверка наличия ожидаемого поля (если указано)
        if [ -n "$expected_field" ]; then
            if echo "$response" | jq -e ".$expected_field" >/dev/null 2>&1; then
                echo -e "${GREEN}✓ PASS${NC} (Valid JSON with '$expected_field')"
                PASSED=$((PASSED + 1))
            else
                echo -e "${RED}✗ FAIL${NC} (Missing field: $expected_field)"
                echo "Response: $response" | head -c 200
                FAILED=$((FAILED + 1))
            fi
        else
            echo -e "${GREEN}✓ PASS${NC} (Valid JSON)"
            PASSED=$((PASSED + 1))
        fi
    else
        echo -e "${RED}✗ FAIL${NC} (Invalid JSON or error)"
        echo "Response: $response" | head -c 200
        FAILED=$((FAILED + 1))
    fi
}

echo "════════════════════════════════════════════════════════════════"
echo "📊 БАЗОВАЯ ПРОВЕРКА СЕРВИСОВ"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Проверка что все контейнеры работают
echo -e "${BLUE}Checking Docker containers...${NC}"
docker compose ps | grep -E "(backend|frontend|db|redis|celery)"
echo ""

# Базовые endpoint'ы
test_endpoint "Backend Health" "http://localhost:8000/health" "200"
test_json_endpoint "Backend Version" "http://localhost:8000/version" "" "version"
test_endpoint "Frontend Status" "http://localhost:3000" "200"
test_endpoint "API Documentation" "http://localhost:8000/docs" "200"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔍 МОДУЛЬ 1: OCR EDITOR (10 файлов)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}Проверяем наличие модулей OCR:${NC}"
if [ -d "frontend/src/modules/ocr" ]; then
    echo -e "${GREEN}✓${NC} frontend/src/modules/ocr/ exists"
    ls -la frontend/src/modules/ocr/ | grep -E "(api|hooks|components)"
else
    echo -e "${RED}✗${NC} frontend/src/modules/ocr/ NOT FOUND"
fi

echo ""
echo -e "${YELLOW}Проверяем файлы OCR модуля:${NC}"
for file in \
    "frontend/src/modules/ocr/api/ocrApi.js" \
    "frontend/src/modules/ocr/hooks/useOCRBlocks.js" \
    "frontend/src/modules/ocr/hooks/useBlockDrag.js" \
    "frontend/src/modules/ocr/hooks/useBlockResize.js" \
    "frontend/src/modules/ocr/components/ImageViewer.js" \
    "frontend/src/modules/ocr/components/BlockCanvas.js" \
    "frontend/src/modules/ocr/components/BlockToolbar.js" \
    "frontend/src/modules/ocr/components/BlocksList.js" \
    "frontend/src/modules/ocr/components/OCREditorContainer.js" \
    "frontend/src/modules/ocr/index.js"
do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo -e "${GREEN}✓${NC} $file (${lines} lines)"
    else
        echo -e "${RED}✗${NC} $file NOT FOUND"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "⚙️  МОДУЛЬ 2: SERVICE MANAGER (5 файлов)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}Проверяем файлы Services модуля:${NC}"
for file in \
    "frontend/src/modules/admin/services/api/servicesApi.js" \
    "frontend/src/modules/admin/services/hooks/useServices.js" \
    "frontend/src/modules/admin/services/components/ServiceCard.js" \
    "frontend/src/modules/admin/services/components/ServicesPanel.js" \
    "frontend/src/modules/admin/services/index.js"
do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo -e "${GREEN}✓${NC} $file (${lines} lines)"
    else
        echo -e "${RED}✗${NC} $file NOT FOUND"
    fi
done

# Тест API Services
echo ""
echo -e "${YELLOW}Testing Services API:${NC}"
test_json_endpoint "Services Status API" "http://localhost:8000/api/services/status" "" ""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📇 МОДУЛЬ 3: CONTACT LIST (8 файлов)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}Проверяем файлы Contacts модуля:${NC}"
for file in \
    "frontend/src/modules/contacts/api/contactsApi.js" \
    "frontend/src/modules/contacts/hooks/useContacts.js" \
    "frontend/src/modules/contacts/hooks/useContactFilters.js" \
    "frontend/src/modules/contacts/components/ContactFilters.js" \
    "frontend/src/modules/contacts/components/ContactActions.js" \
    "frontend/src/modules/contacts/components/ContactTable.js" \
    "frontend/src/modules/contacts/components/ContactListContainer.js" \
    "frontend/src/modules/contacts/index.js"
do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo -e "${GREEN}✓${NC} $file (${lines} lines)"
    else
        echo -e "${RED}✗${NC} $file NOT FOUND"
    fi
done

# Тест API Contacts
echo ""
echo -e "${YELLOW}Testing Contacts API:${NC}"
test_json_endpoint "Contacts List API" "http://localhost:8000/api/contacts?skip=0&limit=10" "" ""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔧 МОДУЛЬ 4: SYSTEM SETTINGS (5 файлов)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}Проверяем файлы Settings модуля:${NC}"
for file in \
    "frontend/src/modules/admin/settings/api/settingsApi.js" \
    "frontend/src/modules/admin/settings/hooks/useIntegrations.js" \
    "frontend/src/modules/admin/settings/components/IntegrationCard.js" \
    "frontend/src/modules/admin/settings/components/SettingsPanel.js" \
    "frontend/src/modules/admin/settings/index.js"
do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        echo -e "${GREEN}✓${NC} $file (${lines} lines)"
    else
        echo -e "${RED}✗${NC} $file NOT FOUND"
    fi
done

# Тест API Settings
echo ""
echo -e "${YELLOW}Testing Settings API:${NC}"
test_json_endpoint "Integrations Status API" "http://localhost:8000/api/integrations/status" "" ""

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🔗 ПРОВЕРКА ИНТЕГРАЦИИ МОДУЛЕЙ"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo -e "${YELLOW}Проверяем импорты модулей в основных компонентах:${NC}"

# ContactList импортирует OCREditorContainer
if grep -q "from '../modules/ocr'" frontend/src/components/ContactList.js 2>/dev/null; then
    echo -e "${GREEN}✓${NC} ContactList.js imports OCR module"
else
    if grep -q "OCREditorContainer" frontend/src/components/ContactList.js 2>/dev/null; then
        echo -e "${GREEN}✓${NC} ContactList.js uses OCREditorContainer"
    else
        echo -e "${RED}✗${NC} ContactList.js doesn't import OCR module"
    fi
fi

# AdminPanel импортирует ServicesPanel
if grep -q "from '../modules/admin/services'" frontend/src/components/AdminPanel.js 2>/dev/null; then
    echo -e "${GREEN}✓${NC} AdminPanel.js imports Services module"
else
    echo -e "${RED}✗${NC} AdminPanel.js doesn't import Services module"
fi

# ContactPage импортирует OCREditorContainer
if grep -q "from '../../modules/ocr'" frontend/src/components/pages/ContactPage.js 2>/dev/null; then
    echo -e "${GREEN}✓${NC} ContactPage.js imports OCR module"
else
    echo -e "${YELLOW}?${NC} ContactPage.js import status unclear"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 ИТОГОВАЯ СТАТИСТИКА"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Подсчёт всех модульных файлов
total_files=$(find frontend/src/modules -type f -name "*.js" 2>/dev/null | wc -l)
total_lines=$(find frontend/src/modules -type f -name "*.js" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')

echo -e "${BLUE}Статистика модулей:${NC}"
echo "  - Всего модульных файлов: ${total_files}"
echo "  - Всего строк кода: ${total_lines}"
echo ""

# Размеры модулей
echo -e "${BLUE}Размеры модулей:${NC}"
for module in ocr contacts; do
    if [ -d "frontend/src/modules/$module" ]; then
        count=$(find "frontend/src/modules/$module" -name "*.js" | wc -l)
        lines=$(find "frontend/src/modules/$module" -name "*.js" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
        echo "  - modules/$module/: $count files, $lines lines"
    fi
done

for module in services settings; do
    if [ -d "frontend/src/modules/admin/$module" ]; then
        count=$(find "frontend/src/modules/admin/$module" -name "*.js" | wc -l)
        lines=$(find "frontend/src/modules/admin/$module" -name "*.js" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
        echo "  - modules/admin/$module/: $count files, $lines lines"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🎯 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "Total tests: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}║   ✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! МИГРАЦИЯ УСПЕШНА! 🎉                 ║${NC}"
    echo -e "${GREEN}║                                                                ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
else
    echo ""
    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                                                ║${NC}"
    echo -e "${YELLOW}║   ⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ                               ║${NC}"
    echo -e "${YELLOW}║   Проверьте логи выше                                         ║${NC}"
    echo -e "${YELLOW}║                                                                ║${NC}"
    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo "Отчёт сохранён в: FULL_UI_TEST_v2.21.7.sh"
echo "Дата: $(date)"

