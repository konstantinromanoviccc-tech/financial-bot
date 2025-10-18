import os
import io
import logging
import requests
import time
import threading
import base64
from flask import Flask, request, jsonify, render_template_string
from openai import OpenAI
import pandas as pd
from PIL import Image
import tempfile

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Инициализация клиента для OpenRouter
client = OpenAI(
    api_key=os.getenv('OPENROUTER_API_KEY'),
    base_url="https://openrouter.ai/api/v1"
)

# Конфигурация
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'txt', 'csv', 'xlsx', 'xls', 'pdf'}
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Ваш промт (ВСТАВЬТЕ ВАШ ПОЛНЫЙ ПРОМТ ЗДЕСЬ)
FINANCIAL_ANALYST_PROMPT = """Ты - финансовый аналитик-консультант с 15-летним опытом работы. Ты специализируешься на внедрении управленческого учета, анализе финансовых данных из 1С, поиске узких мест в бизнес-процессах, расчете юнит-экономики и помощи в работе с банками.

# ПРЕДПОСЫЛКИ И ПРИНЦИПЫ РАБОТЫ:
1. РАБОТА С НЕПОЛНЫМИ ДАННЫМИ - если каких-то данных нет, используй доступные показатели и делай предположения на основе отраслевых нормативов и логики
2. ПРИОРИТЕТ ДОСТУПНОЙ ИНФОРМАЦИИ - всегда выжимай максимум из имеющихся данных, даже если их недостаточно для полного анализа
3. ПРОПУСК НЕДОСТУПНЫХ РАЗДЕЛОВ - если данных для определенного раздела нет полностью, пропускай этот анализ, но указывай, что нужно для его проведения
4. ГИБКОСТЬ И ПРАКТИЧНОСТЬ - давай рекомендации, которые можно реализовать даже при ограниченной информации

# СТРУКТУРА ОТВЕТА:
1. КРАТКОЕ РЕЗЮМЕ - основные выводы по доступным данным
2. ДЕТАЛЬНЫЙ АНАЛИЗ - только по направлениям с имеющимися данными  
3. РЕКОМЕНДАЦИИ - конкретные шаги на основе доступной информации
4. ПЛАН ДЕЙСТВИЙ - приоритетные меры на ближайший период
5. ЧТО НУЖНО ДОПОЛНИТЕЛЬНО - список недостающих данных для более точного анализа

# БАЗА ЗНАНИЙ ДЛЯ АНАЛИЗА:

**РАЗДЕЛ 1: ФИНАНСОВЫЙ ЦИКЛ - ИНДИКАТОР ЭФФЕКТИВНОСТИ ВАШЕГО БИЗНЕСА**

**Простыми словами:**
Финансовый цикл - это количество дней, когда ваши деньги "заморожены" в бизнесе.
- **Хорошо:** когда цикл короткий или отрицательный (деньги быстро возвращаются)
- **Плохо:** когда цикл длинный (деньги надолго застревают в запасах и долгах клиентов)

**Ваша задача:** постоянно сокращать этот показатель

### АНАЛИЗ ТЕКУЩЕЙ СИТУАЦИИ И ОТКЛОНЕНИЙ ЗА ПОСЛЕДНИЙ МЕСЯЦ

**По данным из вашей 1С мы видим:**

**ДЕБИТОРСКАЯ ЗАДОЛЖЕННОСТЬ:**
- Текущая оборачиваемость: [X] дней
- Изменение за месяц: [+15%] 📈 (тревожный сигнал)
- Проблема: дебиторка старше 90 дней на сумму [Z] рублей

**Причины роста дебиторки:**
- Увеличение отсрочки для ключевых клиентов
- Сезонное замедление платежей
- Проблемы с взысканием долгов
- Изменение условий договоров

**10 ИНСТРУМЕНТОВ ДЛЯ ДЕБИТОРКИ:**
1. Предоплата 30-50% для новых клиентов
2. Факторинг проблемной дебиторки
3. Автоматические напоминания за 7-3-1 день до оплаты
4. Скидка 3-5% за оплату в течение 5 дней
5. Банковские гарантии на авансы
6. Поэтапная оплата по проектам
7. Залоги и поручительства по крупным сделкам
8. Реструктуризация долга с графиком платежей
9. Переуступка прав требований коллекторам
10. Подача исков в суд по безнадежным долгам

**ЗАПАСЫ:**
- Текущая оборачиваемость: [Y] дней
- Изменение за месяц: [-8%] 📉 (положительная динамика)
- Неликвидные запасы (не оборачивались 90+ дней)

**10 ИНСТРУМЕНТОВ ДЛЯ ЗАПАСОВ:**
1. Срочная распродажа неликвидов со скидкой 30-70%
2. Возврат поставщикам по согласованию
3. Переработка в другие продукты
4. Уценка до себестоимости
5. Обмен с другими компаниями
6. Создание пакетных предложений
7. Использование в качестве бонусов клиентам
8. Сдача в аренду или лизинг
9. Донация на благотворительность (налоговые выгоды)
10. Утилизация и списание с налоговой экономией

**КРЕДИТОРСКАЯ ЗАДОЛЖЕННОСТЬ:**
- Текущая оборачиваемость: [Z] дней
- Изменение за месяц: [+12%] 📈 (улучшение условий)

**10 ИНСТРУМЕНТОВ ДЛЯ КРЕДИТОРКИ:**
1. Переговоры об увеличении отсрочки до 45-60 дней
2. Поиск альтернативных поставщиков с лучшими условиями
3. Объединение закупок для увеличения объема и улучшения условий
4. Взаимозачеты с контрагентами
5. Использование аккредитивов для отсрочки платежей
6. Лизинг вместо покупки оборудования
7. Оплата по факту реализации товара
8. Использование электронных площадок для тендеров
9. Участие в программах лояльности поставщиков
10. Бартерные сделки вместо денежных расчетов

### УПРАВЛЕНИЕ ОТКЛОНЕНИЯМИ

**При отклонениях более 10% рекомендуем:**
**Если отклонение негативное (рост дебиторки/запасов):**
- Немедленный анализ причин с менеджерами
- Введение лимитов по отсрочкам
- Корректировка планов закупок
- Внедрение дополнительного контроля

**Если отклонение позитивное (улучшение показателей):**
- Закрепление успешных практик
- Масштабирование на другие направления
- Мотивация ответственных сотрудников
- Внедрение в стандартные процедуры

### СРАВНЕНИЕ С ОТРАСЛЕВЫМИ НОРМАТИВАМИ

**Для [ваша отрасль]:**
- Норматив оборачиваемости дебиторки: 20-30 дней
- Норматив оборачиваемости запасов: 15-25 дней
- Норматив по кредиторке: 40-60 дней

**Ваши показатели:**
- Дебиторка: [X] дней (🔴 выше нормы / 🟢 в норме)
- Запасы: [Y] дней (🔴 выше нормы / 🟢 в норме)
- Кредиторка: [Z] дней (🔴 ниже нормы / 🟢 в норме)

**РАЗДЕЛ 2: ЛИКВИДНОСТЬ БАЛАНСА - РЕАЛЬНАЯ ПЛАТЕЖЕСПОСОБНОСТЬ ВАШЕГО БИЗНЕСА**

**Что показывает ликвидность:**
Способность компании своевременно оплачивать обязательства за счет быстрой конвертации активов в деньги.

**Ключевой показатель: СОК (собственный оборотный капитал)**
**Базовая формула:** СОК = Оборотные активы - Краткосрочные обязательства

### РЕАЛЬНАЯ ОЦЕНКА ЛИКВИДНОСТИ С УЧЕТОМ КАЧЕСТВА АКТИВОВ

**По данным вашей 1С выявлено:**
**КОРРЕКТИРОВКА СОК С УЧЕТОМ РИСКОВ:**
- Номинальный СОК: [X] рублей
- Дебиторка >90 дней: [Y] рублей (неликвидная)
- Необорачиваемые запасы: [Z] рублей (неликвидные)
- **Реальный СОК:** [X - Y - Z] рублей

**10 ИНСТРУМЕНТОВ ДЛЯ УЛУЧШЕНИЯ ЛИКВИДНОСТИ**

**ДЛЯ ДЕБИТОРСКОЙ ЗАДОЛЖЕННОСТИ:**
1. Факторинг проблемной дебиторки со скидкой 15-20%
2. Реструктуризация долга с графиком платежей
3. Переуступка прав требований коллекторам
4. Подача исковых заявлений в суд
5. Взаимозачеты с контрагентами

**ДЛЯ НЕЛИКВИДНЫХ ЗАПАСОВ:**
6. Срочная распродажа со скидкой 40-70%
7. Возврат поставщикам по согласованию
8. Переработка в другие продукты
9. Бартерный обмен с другими компаниями
10. Утилизация с налоговой экономией

**РАЗДЕЛ 3: ЮНИТ-ЭКОНОМИКА -- КОНКРЕТНЫЕ РЕШЕНИЯ НА ОСНОВЕ АНАЛИЗА ДАННЫХ 1С**

**Формула прибыли в разрезе юнит-экономики:**
`Прибыль = Охват шт. * К1 * К2 * К3 * (Средний чек - Пер.Расходы ед.) * Повтор - Пост.Расходы - Маркетинг ед. * Охват шт.`

**Источник данных:** Все расчеты выполняются на основе оперативных данных **1С:Предприятие**.

### **АНАЛИЗ И РЕШЕНИЯ ПО КАЖДОМУ ЭЛЕМЕНТУ ФОРМУЛЫ**

#### **1. ОХВАТ (Трафик) -- Решение: Где искать клиентов**

**Анализ в 1С:** Отчет **«Анализ доходов и расходов по статьям ДДС»** (Раздел «Отчеты» -> «Отчеты по денежным средствам»). Фильтруем по статьям «Маркетинг» и «Реклама», группируем по подразделениям (каналам).

**✅ КОНКРЕТНЫЕ РЕШЕНИЯ ДЛЯ ОХВАТА (на основе 1С):**
1. **Скачать из 1С отчет «Оборотно-сальдовая ведомость по счету 44.01 "Издержки обращения"»**. Проанализировать, по каким статьям маркетинга самые высокие расходы при низкой отдаче. Перераспределить бюджет.
2. **Внедрить ежедневный план на основе данных 1С:** В отчете **«Продажи по менеджерам»** определить среднюю дневную конверсию (K1) лучшего менеджера. Установить эту цифру как план для всех: *X звонков в день, приводящих к Y заявкам*.
3. **Определить WHO по данным 1С:** В отчете **«Анализ продаж по контрагентам»** отфильтровать Top-10 самых прибыльных клиентов. Выписать их общие признаки (регион, сфера деятельности, объем закупок). Это и есть ваш "идеальный клиент".

#### **2. КОНВЕРСИИ (К1, К2, К3) -- Решение: Как увеличить процент продаж**

**✅ КОНКРЕТНЫЕ РЕШЕНИЯ ДЛЯ КОНВЕРСИИ (на основе 1С):**
1. **Скачать из 1С «Отчет по реализации»** по товарам с самой низкой оборачиваемостью. Это "неизвестные" клиенту товары. **Для них создать новые УТП и заголовки** и протестировать в рекламе.
2. **Проанализировать в 1С «Возвраты от покупателей»** и **«Регистр накопления "Журнал диалогов"»** (если есть). Выявить частые причины отказов. Создать 3 информационных поста/инструкции, которые снимают эти возражения.

#### **3. СРЕДНИЙ ЧЕК -- Решение: Как увеличить сумму покупки**

**✅ КОНКРЕТНЫЕ РЕШЕНИЯ ДЛЯ СРЕДНЕГО ЧЕКА (на основе 1С):**
1. **Из отчета 1С «Часто покупаемые вместе»** выявить 2-3 самых популярных связки товаров. Оформить их как готовый пакет в **«Номенклатуре»** с специальной ценой. Обучить менеджеров предлагать его.
2. **Создать в 1С новый тип номенклатуры «Дополнительная услуга»** (например, "расширенная гарантия", "установка"). Настроить его автоматическое добавление в каждый документ «Реализация товаров и услуг».

#### **4. ПОСТОЯННЫЕ РАСХОДЫ -- Решение: Как снизить "груз"**

**✅ КОНКРЕТНЫЕ РЕШЕНИЯ ДЛЯ ПОСТОЯННЫХ РАСХОДОВ (на основе 1С):**
1. **Проанализировать в 1С «Отчет по зарплате»** и долю оклада в ФОТ. Внедрить KPI для офисных сотрудников, привязав часть оклада к выполнению плана продаж или операционных показателей.
2. **Из отчета 1С «Расходы по статьям»** выявить самые затратные статьи (аренда, связь, ПО). Найти способы перевода их в переменные: пересмотреть тарифы, перейти на более дешевых провайдеров, часть функций отдать на аутсорс.

#### **5. ВОЗВРАТ К ПОКУПКЕ (ПОВТОР) -- Решение: Как вернуть клиента**

**✅ КОНКРЕТНЫЕ РЕШЕНИЯ ДЛЯ ВОЗВРАТА (на основе 1С):**
1. **Настроить в 1С автоматическое создание задачи менеджеру** через **«Бизнес-процессы»** по истечении X дней с последней покупки ключевого клиента.
2. **Внести в 1С в карточки всех клиентов поля «Дата рождения» и «Источник привлечения»**. Настроить автоматическую рассылку поздравлений и персональных предложений.

**РАЗДЕЛ 4: АНАЛИЗ ДЕНЕЖНЫХ ПОТОКОВ - ОТЧЕТ О ДВИЖЕНИИ ДЕНЕЖНЫХ СРЕДСТВ**

**Что показывает отчет ДДС:**
Реальная картина движения денег на ваших счетах 50, 51, 52, 55. Прибыль в учете ≠ деньги на счетах.

### РЕТРОСПЕКТИВНЫЙ АНАЛИЗ ДДС ЗА ПОСЛЕДНИЙ КВАРТАЛ

**ОПЕРАЦИОННАЯ ДЕЯТЕЛЬНОСТЬ (ТЕКУЩИЕ ОПЕРАЦИИ):**
- Приток: [X] рублей (поступления от клиентов, авансы)
- Отток: [Y] рублей (поставщики, зарплата, налоги)
- Чистый операционный поток: [X-Y] рублей

**ИНВЕСТИЦИОННАЯ ДЕЯТЕЛЬНОСТЬ (РАЗВИТИЕ):**
- Приток: [A] рублей (продажа оборудования)
- Отток: [B] рублей (покупка основных средств)
- Чистый инвестиционный поток: [A-B] рублей

**ФИНАНСОВАЯ ДЕЯТЕЛЬНОСТЬ (КРЕДИТЫ/ИНВЕСТИЦИИ):**
- Приток: [C] рублей (кредиты, инвестиции)
- Отток: [D] рублей (выплата дивидендов, погашение кредитов)
- Чистый финансовый поток: [C-D] рублей

### РЕКОМЕНДАЦИИ ПО УПРАВЛЕНИЮ ДЕНЕЖНЫМИ ПОТОКАМИ

**ДЛЯ ОПЕРАЦИОННОГО ПОТОКА:**
1. Внедрить предоплату для новых клиентов
2. Оптимизировать сроки оплаты поставщикам
3. Создать систему скидок за ранние платежи
4. Автоматизировать инкассацию дебиторки

**ДЛЯ ИНВЕСТИЦИОННОГО ПОТОКА:**
5. Внедрить ROI-анализ для всех проектов
6. Использовать лизинг вместо покупки
7. Создать реестр приоритетных инвестиций
8. Реализовать неиспользуемые активы

**ДЛЯ ФИНАНСОВОГО ПОТОКА:**
9. Рефинансировать дорогие кредиты
10. Диверсифицировать источники финансирования

**РАЗДЕЛ 5: БАНКОВСКИЕ ПОКАЗАТЕЛИ - ОЦЕНКА КРЕДИТОСПОСОБНОСТИ**

**Что оценивают банки:**
Способность компании генерировать денежные потоки для обслуживания долга и устойчивость бизнес-модели.

### КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ ДЛЯ БАНКОВ

**1. ДОЛГ/EBITDA:**
- **Ваш показатель:** [X] (норма: <4.0, для вашей отрасли: <3.5)
- **Динамика:** [+0.3] за последний квартал

**2. EBITDA/ПРОЦЕНТЫ:**
- **Ваш показатель:** [Z] (норма: >1.5)
- **Динамика:** [-0.2] за последний квартал

**3. ЧИСТАЯ ПРИБЫЛЬ/ПРОЦЕНТЫ:**
- **Ваш показатель:** [A] (норма: >1.0)
- **Динамика:** [+0.1] за квартал

### 10 ИНСТРУМЕНТОВ ДЛЯ УЛУЧШЕНИЯ ПОКАЗАТЕЛЕЙ

**ДЛЯ EBITDA:**
1. **Оптимизация себестоимости** через пересмотр поставщиков
2. **Реструктуризация долга** с уменьшением процентной нагрузки
3. **Продажа непрофильных активов** для роста EBITDA
4. **Снижение операционных расходов** на 10-15%

**ДЛЯ ОБОРАЧИВАЕМОСТИ:**
5. **Факторинг дебиторки** для ускорения оборачиваемости
6. **Распродажа неликвидов** со скидкой 30-50%
7. **Переговоры с поставщиками** об увеличении отсрочки
8. **Внедрение предоплаты** для новых клиентов

**ДЛЯ СОК:**
9. **Рефинансирование краткосрочных кредитов**
10. **Привлечение инвестиций** в оборотный капитал

**РАЗДЕЛ 6: НАЛОГОВЫЕ РИСКИ -- ПРЕВЕНТИВНЫЙ АНАЛИЗ ДО НАЧИСЛЕНИЯ НАЛОГОВ**

**Что оцениваем:**
Риски доначислений налогов, пеней и штрафов на этапе формирования операций. **Главный вопрос:** "Верно ли мы отражаем операции в 1С с точки зрения НК РФ *до* того, как они попадут в декларации?"

### КЛЮЧЕВЫЕ НАПРАВЛЕНИЯ ДЛЯ КОНТРОЛЯ

**1. НДС: Риск необоснованного вычета:**
- **Что проверять:** Регистры "Накопленные покупки" и счета-фактуры в 1С.
- **Критерий риска:** Отсутствие первичных документов, контрагенты-однодневки, несоответствие дат.

**2. Налог на прибыль: Риск непризнания расходов:**
- **Что проверять:** Оприходование ТМЦ, акты выполненных работ, списание затрат (счета 20, 26, 44).
- **Критерий риска:** Отсутствие ЭД, экономическая необоснованность, превышение нормируемых расходов.

**3. Страховые взносы и НДФЛ: Риск неполной базы:**
- **Что проверять:** Начисления по сотрудникам (счет 70), выплаты по ГПД (счет 76).
- **Критерий риска:** Не включены в базу мат. помощь > 4000 руб., подарки, выплаты по неверно оформленным ГПД.

### 10 ИНСТРУМЕНТОВ ДЛЯ СНИЖЕНИЯ НАЛОГОВЫХ РИСКОВ

**Для НДС:**
1. **Усиление проверки контрагентов** перед отгрузкой/оплатой.
2. **Автоматический контроль сроков выставления счетов-фактур** в 1С.
3. **Сверка с поставщиками** по неполученным счетам-фактурам.

**Для налога на прибыль:**
4. **Внедрение правил документооборота** для всех хозяйственных операций.
5. **Настройка в 1С предупредительных сообщений** о нормируемых расходах.
6. **Регулярный анализ постоянных и временных разниц** (ПБУ 18/02).

**Для зарплаты и взносов:**
7. **Аудит трудовых и ГПД договоров** на соответствие ТК РФ.
8. **Четкий регламент учета подарков и мат.помощи**.
9. **Сверка начислений и уплаты взносов с расчетами по форме РСВ**.

**Общие:**
10. **Внедрение ежемесячного налогового мониторинга** по чек-листу.

# ИНСТРУКЦИЯ ДЛЯ АНАЛИТИКА:

При получении данных из 1С:
1. Проведи анализ по ВСЕМ разделам базы знаний, где есть соответствующие данные
2. Заменяй все placeholders ([X], [Y], [Z], [ваша отрасль] и т.д.) на реальные цифры из данных клиента
3. Давай конкретные рекомендации с указанием точных сумм и сроков
4. Предлагай готовый план действий на ближайший месяц
5. Всегда сравнивай показатели с отраслевыми нормативами
6. Указывай финансовый эффект от внедрения рекомендаций

Отвечай на русском языке, используй профессиональную но понятную бизнесу терминологию. Структурируй ответ с помощью заголовков, таблиц и маркированных списков для лучшей читаемости.

# ИНСТРУКЦИЯ ДЛЯ АНАЛИТИКА:
При получении данных из 1С проводи анализ по ВСЕМ разделам базы знаний, где есть соответствующие данные. Заменяй все placeholders ([X], [Y], [Z], [ваша отрасль] и т.д.) на реальные цифры из данных клиента. Давай конкретные рекомендации с указанием точных сумм и сроков. Всегда сравнивай показатели с отраслевыми нормативами.

Отвечай на русском языке, используй профессиональную но понятную бизнесу терминологию. Структурируй ответ с помощью заголовков, таблиц и маркированных списков для лучшей читаемости. Будь практичным и полезным даже при ограниченной информации."""

def analyze_financial_data(user_data):
    """Функция для анализа финансовых данных через OpenRouter API"""
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": FINANCIAL_ANALYST_PROMPT},
                {"role": "user", "content": user_data}
            ],
            stream=False,
            temperature=0.1,
            extra_headers={
                "HTTP-Referer": "https://financial-bot-euho.onrender.com",
                "X-Title": "Financial Analyst Bot",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка при обращении к OpenRouter API: {str(e)}")
        return "❌ Произошла ошибка при анализе данных. Пожалуйста, попробуйте еще раз."

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file_data(file):
    try:
        filename = file.filename.lower()
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
            return df.to_string()
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
            return df.to_string()
        elif filename.endswith('.txt'):
            return file.read().decode('utf-8')
        else:
            return None
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {str(e)}")
        return None

def send_telegram_message(chat_id, text):
    """Отправка сообщения в Telegram БЕЗ HTML разметки"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен")
        return False
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Разбиваем длинные сообщения на части
    max_length = 4000
    if len(text) > max_length:
        parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        for part in parts:
            payload = {
                "chat_id": chat_id,
                "text": part
                # НЕТ parse_mode - отправляем как обычный текст
            }
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code != 200:
                    logger.error(f"Ошибка отправки в Telegram: {response.text}")
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Ошибка отправки в Telegram: {str(e)}")
                return False
        return True
    else:
        payload = {
            "chat_id": chat_id,
            "text": text
            # НЕТ parse_mode - отправляем как обычный текст
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Ошибка отправки в Telegram: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {str(e)}")
            return False

def download_telegram_file(file_id):
    """Скачивание файла из Telegram"""
    try:
        # Получаем информацию о файле
        file_info_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile"
        file_info_response = requests.post(file_info_url, json={"file_id": file_id})
        file_info = file_info_response.json()
        
        if not file_info.get('ok'):
            return None
            
        file_path = file_info['result']['file_path']
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        
        # Скачиваем файл
        file_response = requests.get(file_url)
        return file_response.content
        
    except Exception as e:
        logger.error(f"Ошибка скачивания файла: {str(e)}")
        return None

def process_image(image_content):
    """Обработка изображения - конвертация в текст через OpenRouter Vision"""
    try:
        # Кодируем изображение в base64
        image_base64 = base64.b64encode(image_content).decode('utf-8')
        
        response = client.chat.completions.create(
            model="openai/gpt-4o",  # Модель с поддержкой vision
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Пожалуйста, прочитайте и проанализируйте это финансовое изображение. Извлеките все числовые данные, текст и таблицы. Если это график - опишите его. Верните структурированные данные в текстовом формате."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка обработки изображения: {str(e)}")
        return f"Не удалось обработать изображение: {str(e)}"

def handle_telegram_message(chat_id, message_data):
    """Обработка сообщения от Telegram в отдельном потоке"""
    try:
        message_text = message_data.get('text', '')
        document = message_data.get('document')
        photo = message_data.get('photo')
        
        # Обработка команд
        if message_text.startswith('/start'):
            welcome_msg = """🤖 Добро пожаловать в Финансовый аналитик!

Я могу анализировать:
• 📊 Текстовые финансовые данные
• 📁 Файлы Excel/CSV
• 🖼️ Фотографии финансовых отчетов
• 💬 Любые финансовые вопросы

Просто отправьте мне данные для анализа!"""
            send_telegram_message(chat_id, welcome_msg)
        
        elif message_text.startswith('/help'):
            help_msg = """📋 Доступные команды:

/start - начать работу
/help - помощь
/analyze - анализ данных

Что я могу анализировать:
• Выручка, прибыль, расходы
• Балансы и отчеты
• Финансовые файлы (Excel, CSV)
• Фотографии отчетов
• Любые финансовые вопросы"""
            send_telegram_message(chat_id, help_msg)
        
        # Обработка документов (Excel, CSV файлы)
        elif document:
            file_id = document['file_id']
            file_name = document.get('file_name', 'файл')
            
            send_telegram_message(chat_id, f"📥 Получил файл: {file_name}. Обрабатываю...")
            
            file_content = download_telegram_file(file_id)
            if file_content:
                # Создаем временный файл для обработки
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_name) as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                
                try:
                    # Обрабатываем файл в зависимости от типа
                    if file_name.lower().endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(temp_file_path)
                        file_data = df.to_string()
                    elif file_name.lower().endswith('.csv'):
                        df = pd.read_csv(temp_file_path)
                        file_data = df.to_string()
                    else:
                        # Для других файлов пробуем прочитать как текст
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            file_data = f.read()
                    
                    analysis_text = f"Данные из файла {file_name}:\n{file_data}"
                    if message_text:
                        analysis_text += f"\n\nКомментарий пользователя: {message_text}"
                    
                    send_telegram_message(chat_id, "🔄 Анализирую данные из файла...")
                    analysis_result = analyze_financial_data(analysis_text)
                    send_telegram_message(chat_id, analysis_result)
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки файла: {str(e)}")
                    send_telegram_message(chat_id, f"❌ Ошибка при обработке файла: {str(e)}")
                finally:
                    # Удаляем временный файл
                    os.unlink(temp_file_path)
            else:
                send_telegram_message(chat_id, "❌ Не удалось загрузить файл. Попробуйте еще раз.")
        
        # Обработка фотографий
        elif photo:
            # Берем последнее (самое качественное) фото
            photo_data = photo[-1]
            file_id = photo_data['file_id']
            
            send_telegram_message(chat_id, "🖼️ Получил изображение. Анализирую...")
            
            image_content = download_telegram_file(file_id)
            if image_content:
                try:
                    # Анализируем изображение
                    image_analysis = process_image(image_content)
                    analysis_text = f"Данные из изображения:\n{image_analysis}"
                    if message_text:
                        analysis_text += f"\n\nКомментарий пользователя: {message_text}"
                    
                    send_telegram_message(chat_id, "🔄 Анализирую распознанные данные...")
                    analysis_result = analyze_financial_data(analysis_text)
                    send_telegram_message(chat_id, analysis_result)
                    
                except Exception as e:
                    logger.error(f"Ошибка анализа изображения: {str(e)}")
                    send_telegram_message(chat_id, f"❌ Ошибка при анализе изображения: {str(e)}")
            else:
                send_telegram_message(chat_id, "❌ Не удалось загрузить изображение. Попробуйте еще раз.")
        
        # Обработка текстовых сообщений
        elif message_text:
            if message_text.startswith('/analyze') or any(word in message_text.lower() for word in ['выручка', 'прибыль', 'дебиторк', 'запас', 'финанс', 'отчет', 'баланс', 'актив', 'пассив', 'кредит', 'заем', 'инвест']):
                send_telegram_message(chat_id, "🔄 Анализирую ваши данные... Это займет несколько секунд.")
                analysis_result = analyze_financial_data(message_text)
                if analysis_result:
                    send_telegram_message(chat_id, analysis_result)
                else:
                    send_telegram_message(chat_id, "❌ Не удалось проанализировать данные. Попробуйте еще раз.")
            else:
                # Анализируем любой текст, даже если он не содержит финансовых ключевых слов
                send_telegram_message(chat_id, "🔄 Анализирую ваш запрос...")
                analysis_result = analyze_financial_data(message_text)
                if analysis_result:
                    send_telegram_message(chat_id, analysis_result)
                else:
                    send_telegram_message(chat_id, "❌ Не удалось проанализировать запрос. Попробуйте еще раз.")
        
        # Если нет ни текста, ни файла, ни фото
        else:
            send_telegram_message(chat_id, "🤔 Не понял ваш запрос. Отправьте текст, файл или фото для анализа.")
            
    except Exception as e:
        logger.error(f"Ошибка в handle_telegram_message: {str(e)}")
        send_telegram_message(chat_id, "❌ Произошла ошибка при обработке запроса. Попробуйте еще раз.")

# HTML шаблон для веб-интерфейса
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Финансовый аналитик</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .tab-buttons {
            display: flex;
            margin-bottom: 20px;
            border-bottom: 1px solid #ddd;
        }
        .tab-btn {
            padding: 12px 24px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            border-bottom: 3px solid transparent;
        }
        .tab-btn.active {
            border-bottom: 3px solid #007bff;
            color: #007bff;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        textarea {
            width: 100%;
            height: 200px;
            margin: 20px 0;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
            font-size: 16px;
            resize: vertical;
        }
        .file-upload {
            border: 2px dashed #ddd;
            padding: 40px;
            text-align: center;
            margin: 20px 0;
            border-radius: 4px;
        }
        .file-upload:hover {
            border-color: #007bff;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            display: block;
            margin: 20px auto;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        #result {
            margin-top: 30px;
            padding: 20px;
            border-radius: 4px;
            display: none;
        }
        .loading {
            color: #856404;
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
        }
        .success {
            color: #155724;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
        }
        .error {
            color: #721c24;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .telegram-info {
            background-color: #0088cc;
            color: white;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Финансовый аналитик</h1>
        <p>Выберите способ ввода данных для финансового анализа</p>
        
        <div class="tab-buttons">
            <button class="tab-btn active" onclick="openTab('text-tab')">Текстовый ввод</button>
            <button class="tab-btn" onclick="openTab('file-tab')">Загрузка файла</button>
        </div>
        
        <!-- Вкладка текстового ввода -->
        <div id="text-tab" class="tab-content active">
            <p>Введите финансовые данные из 1С в поле ниже:</p>
            <textarea id="dataInput" placeholder="Пример:
Выручка: 5 000 000 руб
Чистая прибыль: 450 000 руб
Дебиторская задолженность: 1 800 000 руб
Запасы: 1 200 000 руб
Кредиторская задолженность: 900 000 руб"></textarea>
            <button onclick="analyzeData('text')" id="analyzeTextBtn">Проанализировать текст</button>
        </div>
        
        <!-- Вкладка загрузки файла -->
        <div id="file-tab" class="tab-content">
            <p>Загрузите файл с финансовыми данными (поддерживаются CSV, Excel, TXT):</p>
            <div class="file-upload">
                <input type="file" id="fileInput" accept=".csv,.xlsx,.xls,.txt" style="display: none;" onchange="handleFileSelect()">
                <button onclick="document.getElementById('fileInput').click()">Выберите файл</button>
                <p id="fileName" style="margin-top: 10px;"></p>
            </div>
            <button onclick="analyzeData('file')" id="analyzeFileBtn" disabled>Проанализировать файл</button>
        </div>
        
        <div class="telegram-info">
            <strong>📱 Также доступно в Telegram!</strong><br>
            Наш бот умеет анализировать:<br>
            • Текстовые запросы • Excel/CSV файлы • Фотографии отчетов
        </div>
        
        <div id="result"></div>
    </div>

    <script>
        function openTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.getElementById(tabName).classList.add('active');
            
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
        }
        
        function handleFileSelect() {
            const fileInput = document.getElementById('fileInput');
            const fileName = document.getElementById('fileName');
            const analyzeFileBtn = document.getElementById('analyzeFileBtn');
            
            if (fileInput.files.length > 0) {
                fileName.textContent = 'Выбран файл: ' + fileInput.files[0].name;
                analyzeFileBtn.disabled = false;
            } else {
                fileName.textContent = '';
                analyzeFileBtn.disabled = true;
            }
        }
        
        function analyzeData(type) {
            let data;
            const resultDiv = document.getElementById('result');
            
            if (type === 'text') {
                data = document.getElementById('dataInput').value;
                button = document.getElementById('analyzeTextBtn');
            } else {
                const fileInput = document.getElementById('fileInput');
                if (!fileInput.files.length) {
                    alert('Пожалуйста, выберите файл.');
                    return;
                }
                data = fileInput.files[0];
                button = document.getElementById('analyzeFileBtn');
            }
            
            if (type === 'text' && !data.trim()) {
                alert('Пожалуйста, введите данные для анализа.');
                return;
            }
            
            button.disabled = true;
            const originalText = button.textContent;
            button.textContent = 'Анализируем...';
            resultDiv.style.display = 'block';
            resultDiv.className = 'loading';
            resultDiv.innerHTML = '🔄 Идет анализ ваших данных. Пожалуйста, подождите...';
            
            const formData = new FormData();
            formData.append('data_type', type);
            
            if (type === 'text') {
                formData.append('financial_data', data);
            } else {
                formData.append('file', data);
            }
            
            fetch('/analyze', {
                method: 'POST',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    resultDiv.className = 'success';
                    resultDiv.innerHTML = '<h3>Результат анализа:</h3><pre style="white-space: pre-wrap;">' + data.analysis + '</pre>';
                } else {
                    throw new Error(data.error || 'Неизвестная ошибка');
                }
            })
            .catch(error => {
                resultDiv.className = 'error';
                resultDiv.innerHTML = '<h3>Ошибка:</h3><p>Не удалось выполнить анализ. Проверьте подключение к интернету и попробуйте снова.</p><p><small>Техническая информация: ' + error.message + '</small></p>';
            })
            .finally(() => {
                button.disabled = false;
                button.textContent = originalText;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Главная страница с интерфейсом загрузки файлов"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "service": "financial-analyst-bot"})

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    """Конечная точка для анализа финансовых данных"""
    try:
        data_type = request.form.get('data_type')
        
        if data_type == 'text':
            financial_data = request.form.get('financial_data', '')
            if not financial_data.strip():
                return jsonify({"error": "Отсутствуют финансовые данные"}), 400
            
            analysis_result = analyze_financial_data(financial_data)
            
        elif data_type == 'file':
            if 'file' not in request.files:
                return jsonify({"error": "Файл не был загружен"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "Файл не выбран"}), 400
            
            if file and allowed_file(file.filename):
                file_data = read_file_data(file)
                if file_data is None:
                    return jsonify({"error": "Не удалось прочитать файл. Проверьте формат файла."}), 400
                
                analysis_result = analyze_financial_data(f"Данные из файла {file.filename}:\n{file_data}")
            else:
                return jsonify({"error": f"Недопустимый тип файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
        else:
            return jsonify({"error": "Неверный тип данных"}), 400
        
        return jsonify({
            "status": "success",
            "analysis": analysis_result
        })
        
    except Exception as e:
        logger.error(f"Ошибка в analyze_endpoint: {str(e)}")
        return jsonify({"error": "Внутренняя ошибка сервера"}), 500

# Telegram вебхук
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Webhook для Telegram бота"""
    try:
        update = request.get_json()
        logger.info(f"Получен запрос от Telegram: {update}")
        
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            message_data = {
                'text': update['message'].get('text', ''),
                'document': update['message'].get('document'),
                'photo': update['message'].get('photo')
            }
            
            # Запускаем обработку в отдельном потоке чтобы избежать таймаута
            thread = threading.Thread(
                target=handle_telegram_message,
                args=(chat_id, message_data)
            )
            thread.daemon = True
            thread.start()
                
        return jsonify({"status": "success"})
        
    except Exception as e:
        logger.error(f"Ошибка в telegram_webhook: {str(e)}")
        return jsonify({"status": "success"})  # Всегда возвращаем success

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
