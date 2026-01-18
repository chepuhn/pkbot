import sqlite3
import telebot
import json
from telebot import types
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========== КОНФИГУРАЦИЯ ==========

TOKEN = '8564157907:AAGpbALZpb-dMkL-9mIpnnccK2tk6xF4-_M'  # Замените на свой токен от @BotFather
DB_PATH = 'computer_parts.db'
WEB_APP_URL = 'https://ваш-сайт.github.io/computer-parts-webapp/'  # Замените на ваш URL

# Проверка токена
if len(TOKEN) < 30 or ':' not in TOKEN:
    print("❌ ОШИБКА: Неправильный формат токена!")
    print("ℹ️  Получите токен у @BotFather в Telegram")
    exit(1)

# Инициализация бота
bot = telebot.TeleBot(TOKEN)
print(f"✅ Бот инициализирован с токеном: {TOKEN[:10]}...")


# ========== ФУНКЦИИ РАБОТЫ С БАЗОЙ ДАННЫХ ==========

def init_database():
    """Инициализация базы данных компьютерных комплектующих"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("📊 Создание таблиц базы данных...")

        # Создаем таблицу категорий
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            icon TEXT,
            slug TEXT UNIQUE
        )
        ''')

        # Создаем таблицу товаров
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            category_id INTEGER NOT NULL,
            image_url TEXT,
            specs TEXT,
            in_stock BOOLEAN DEFAULT TRUE,
            rating REAL DEFAULT 0,
            brand TEXT,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
        ''')

        # Создаем таблицу заказов
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            products TEXT,
            total_price REAL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Проверяем, есть ли данные в таблице categories
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            print("📝 Заполняем таблицу категорий...")
            categories_data = [
                ('Процессоры', 'Центральные процессоры (CPU)', '⚡', 'cpu'),
                ('Видеокарты', 'Графические процессоры (GPU)', '🎮', 'gpu'),
                ('Материнские платы', 'Системные платы', '🖥️', 'motherboards'),
                ('Оперативная память', 'Модули RAM', '💾', 'ram'),
                ('Накопители', 'SSD и HDD накопители', '💿', 'storage'),
                ('Блоки питания', 'Источники питания (PSU)', '🔌', 'psu'),
                ('Корпуса', 'Корпуса для ПК', '📦', 'cases'),
                ('Охлаждение', 'Системы охлаждения', '❄️', 'cooling'),
                ('Мониторы', 'Мониторы и дисплеи', '🖥️', 'monitors'),
                ('Клавиатуры и мыши', 'Периферийные устройства', '⌨️', 'peripherals')
            ]
            cursor.executemany(
                "INSERT INTO categories (name, description, icon, slug) VALUES (?, ?, ?, ?)",
                categories_data
            )
            print(f"✅ Добавлено {len(categories_data)} категорий")

        # Проверяем, есть ли данные в таблице products
        cursor.execute("SELECT COUNT(*) FROM products")
        if cursor.fetchone()[0] == 0:
            print("📝 Заполняем таблицу товаров...")
            # Получаем ID категорий
            cursor.execute("SELECT id, slug FROM categories")
            category_map = {slug: id for id, slug in cursor.fetchall()}

            products_data = [
                # Процессоры
                ('AMD Ryzen 5 7600X', '6-ядерный процессор для игр', 24999.0,
                 category_map['cpu'], 'https://example.com/cpu1.jpg',
                 'Сокет: AM5 | Ядра: 6 | Потоки: 12 | Частота: 4.7-5.3 ГГц | Кэш L3: 32 МБ',
                 True, 4.8, 'AMD'),
                ('Intel Core i5-13400F', 'Процессор для офиса и игр', 19850.0,
                 category_map['cpu'], 'https://example.com/cpu2.jpg',
                 'Сокет: LGA1700 | Ядра: 10 (6P+4E) | Потоки: 16 | Частота: 2.5-4.6 ГГц',
                 True, 4.6, 'Intel'),
                ('AMD Ryzen 7 7800X3D', 'Игровой процессор с технологией 3D V-Cache', 37999.0,
                 category_map['cpu'], 'https://example.com/cpu3.jpg',
                 'Сокет: AM5 | Ядра: 8 | Потоки: 16 | Частота: 4.2-5.0 ГГц | Кэш L3: 96 МБ',
                 True, 4.9, 'AMD'),

                # Видеокарты
                ('ASUS TUF RTX 4060 Ti', 'Игровая видеокарта', 48990.0,
                 category_map['gpu'], 'https://example.com/gpu1.jpg',
                 'Память: 8 ГБ GDDR6 | Частота: 2310 МГц | Разъемы: 3xDP, 1xHDMI | Длина: 300 мм',
                 True, 4.7, 'ASUS'),
                ('GIGABYTE RX 7700 XT', 'Видеокарта для 1440p игр', 42999.0,
                 category_map['gpu'], 'https://example.com/gpu2.jpg',
                 'Память: 12 ГБ GDDR6 | Частота: 2171 МГц | Разъемы: 3xDP, 1xHDMI',
                 True, 4.6, 'GIGABYTE'),

                # Материнские платы
                ('ASUS ROG STRIX B650-A', 'Игровая материнская плата', 21999.0,
                 category_map['motherboards'], 'https://example.com/mb1.jpg',
                 'Сокет: AM5 | Форм-фактор: ATX | Память: DDR5 | Слоты M.2: 3',
                 True, 4.8, 'ASUS'),
                ('MSI PRO B760-P', 'Материнская плата для офиса', 14999.0,
                 category_map['motherboards'], 'https://example.com/mb2.jpg',
                 'Сокет: LGA1700 | Форм-фактор: ATX | Память: DDR4 | Слоты M.2: 2',
                 True, 4.5, 'MSI'),

                # Оперативная память
                ('Kingston FURY Beast 32GB', 'Оперативная память DDR5', 7850.0,
                 category_map['ram'], 'https://example.com/ram1.jpg',
                 'Объем: 32 ГБ (2x16) | Частота: 6000 МГц | Тайминги: CL36 | Напряжение: 1.35В',
                 True, 4.7, 'Kingston'),
                ('Corsair Vengeance 16GB', 'Игровая память RGB', 5990.0,
                 category_map['ram'], 'https://example.com/ram2.jpg',
                 'Объем: 16 ГБ (2x8) | Частота: 3600 МГц | Тайминги: CL18 | Подсветка: RGB',
                 True, 4.6, 'Corsair'),

                # Накопители
                ('Samsung 980 Pro 1TB', 'NVMe SSD накопитель', 9990.0,
                 category_map['storage'], 'https://example.com/ssd1.jpg',
                 'Форм-фактор: M.2 2280 | Интерфейс: PCIe 4.0 | Скорость чтения: 7000 МБ/с | Запись: 5000 МБ/с',
                 True, 4.9, 'Samsung'),
                ('WD Blue SN580 2TB', 'Игровой SSD', 12990.0,
                 category_map['storage'], 'https://example.com/ssd2.jpg',
                 'Форм-фактор: M.2 2280 | Интерфейс: PCIe 4.0 | Скорость чтения: 4150 МБ/с',
                 True, 4.7, 'Western Digital'),

                # Блоки питания
                ('be quiet! Pure Power 12 750W', 'Мощный блок питания', 10390.0,
                 category_map['psu'], 'https://example.com/psu1.jpg',
                 'Мощность: 750 Вт | Сертификат: 80+ Gold | Модульный: Полумодульный | Вентилятор: 120 мм',
                 True, 4.8, 'be quiet!'),

                # Корпуса
                ('NZXT H5 Flow', 'Корпус с хорошим охлаждением', 7200.0,
                 category_map['cases'], 'https://example.com/case1.jpg',
                 'Форм-фактор: Mid-Tower | Материал: Сталь, стекло | Вентиляторы: 2x120 мм | Подсветка: Нет',
                 True, 4.6, 'NZXT'),

                # Охлаждение
                ('DeepCool AK620', 'Башенный кулер', 5499.0,
                 category_map['cooling'], 'https://example.com/cooler1.jpg',
                 'Тип: Воздушное | TDP: 260 Вт | Вентиляторы: 2x120 мм | Высота: 160 мм | Подсветка: Нет',
                 True, 4.7, 'DeepCool'),

                # Мониторы
                ('Samsung Odyssey G5', 'Игровой монитор', 29990.0,
                 category_map['monitors'], 'https://example.com/monitor1.jpg',
                 'Диагональ: 27" | Разрешение: 2560x1440 | Частота: 144 Гц | Панель: VA | Изгиб: 1000R',
                 True, 4.8, 'Samsung'),

                # Клавиатуры
                ('Logitech G Pro X', 'Механическая игровая клавиатура', 11990.0,
                 category_map['peripherals'], 'https://example.com/kb1.jpg',
                 'Тип: Механическая | Переключатели: GX Brown | Подсветка: RGB | Формат: TKL',
                 True, 4.7, 'Logitech'),
                ('Razer DeathAdder V3', 'Игровая мышь', 8990.0,
                 category_map['peripherals'], 'https://example.com/mouse1.jpg',
                 'Тип: Проводная | DPI: 30000 | Кнопки: 8 | Вес: 59 г | Сенсор: Focus Pro 30K',
                 True, 4.8, 'Razer')
            ]

            cursor.executemany('''
                INSERT INTO products (name, description, price, category_id, image_url, specs, in_stock, rating, brand) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', products_data)
            print(f"✅ Добавлено {len(products_data)} товаров")

        conn.commit()
        conn.close()
        logger.info("✅ База данных инициализирована")

    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации БД: {e}")
        raise


def get_db_connection():
    """Создание соединения с базой данных"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def check_database():
    """Проверка содержимого базы данных"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM categories")
        category_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM orders")
        order_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT c.name, COUNT(p.id) as product_count
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY product_count DESC
        """)
        category_stats = cursor.fetchall()

        conn.close()

        print(f"\n📊 База данных содержит:")
        print(f"   • Категорий: {category_count}")
        print(f"   • Товаров: {product_count}")
        print(f"   • Заказов: {order_count}")

        print(f"\n📈 Распределение товаров по категориям:")
        for stat in category_stats:
            print(f"   • {stat['name']}: {stat['product_count']} товаров")

        return True

    except Exception as e:
        print(f"❌ Ошибка при проверке БД: {e}")
        return False


# ========== КОМАНДЫ БОТА ==========

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Приветственное сообщение с Web App кнопкой"""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

    user_name = message.from_user.first_name
    welcome_text = f"""
🖥️ *Привет, {user_name}! Добро пожаловать в магазин компьютерных комплектующих!* 🚀

*Новые возможности:*
• 📱 **Современный Web-интерфейс** - нажмите кнопку ниже
• 🎯 **Удобный выбор категорий** с иконками
• ⚡ **Быстрый подбор** комплектующих

*Основные функции:*
• Просмотр каталога по категориям
• Поиск товаров по названию
• Просмотр характеристик и цен
• Информация о наличии на складе

*Для начала работы нажмите:* «🛒 Открыть каталог товаров»
    """

    # Создаем Web App кнопку
    web_app = types.WebAppInfo(url=WEB_APP_URL)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Кнопка для открытия Web App
    web_app_btn = types.KeyboardButton(
        text="🛒 Открыть каталог товаров",
        web_app=web_app
    )

    # Обычные кнопки
    categories_btn = types.KeyboardButton('📁 Категории товаров')
    search_btn = types.KeyboardButton('🔍 Поиск товаров')
    cart_btn = types.KeyboardButton('🛍️ Корзина')
    orders_btn = types.KeyboardButton('📋 Мои заказы')
    stats_btn = types.KeyboardButton('📊 Статистика')
    help_btn = types.KeyboardButton('🆘 Помощь')

    keyboard.add(web_app_btn)
    keyboard.add(categories_btn, search_btn)
    keyboard.add(cart_btn, orders_btn)
    keyboard.add(stats_btn, help_btn)

    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['help', 'помощь'])
def help_command(message):
    """Справка по использованию бота"""
    help_text = """
🆘 *Справка по магазину компьютерных комплектующих*

*Как использовать:*
1. *Web-интерфейс* - нажмите «🛒 Открыть каталог товаров»
2. Выберите категорию и получите список товаров
3. Или используйте традиционные команды ниже

*Основные команды:*
/start - Главное меню
/help - Эта справка
/web - Прямая ссылка на Web App
/categories - Список всех категорий
/search - Поиск товаров
/stats - Статистика магазина
/cart - Показать корзину

*Традиционное меню:*
• 📁 Категории товаров - список всех категорий
• 🔍 Поиск товаров - поиск по названию
• 🛍️ Корзина - просмотр корзины
• 📋 Мои заказы - история заказов
• 📊 Статистика - информация о магазине
• 🆘 Помощь - эта справка

*Советы:*
• Используйте Web App для удобного выбора товаров
• При поиске указывайте полное название
• Проверяйте наличие товара перед оформлением заказа
    """

    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')


@bot.message_handler(commands=['web', 'интерфейс'])
def web_app_command(message):
    """Отправка прямой ссылки на Web App"""
    web_app = types.WebAppInfo(url=WEB_APP_URL)

    keyboard = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton(
        text="🖥️ Открыть каталог товаров",
        web_app=web_app
    )
    keyboard.add(web_btn)

    response = "🛒 *Откройте каталог товаров в Web App*\n\n"
    response += "Нажмите кнопку ниже для открытия современного интерфейса с выбором категорий."

    bot.send_message(
        message.chat.id,
        response,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


@bot.message_handler(commands=['categories', 'категории'])
def categories_command(message):
    """Показать все категории"""
    show_all_categories(message)


@bot.message_handler(commands=['stats', 'статистика'])
def stats_command(message):
    """Статистика магазина"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM products WHERE in_stock = 1")
        in_stock_products = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT brand) FROM products")
        total_brands = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(price), MAX(price), AVG(price) FROM products")
        price_stats = cursor.fetchone()
        min_price, max_price, avg_price = price_stats

        cursor.execute("""
            SELECT c.name, COUNT(p.id) as count 
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id 
            ORDER BY count DESC
            LIMIT 5
        """)
        top_categories = cursor.fetchall()

        cursor.execute("""
            SELECT name, price, rating 
            FROM products 
            WHERE rating >= 4.5 
            ORDER BY rating DESC 
            LIMIT 5
        """)
        top_rated = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0]

        conn.close()

        response = f"""
📊 *Статистика магазина компьютерных комплектующих:*

• Всего товаров: *{total_products}*
• В наличии: *{in_stock_products}* ({in_stock_products / total_products * 100:.1f}%)
• Брендов: *{total_brands}*
• Всего заказов: *{total_orders}*

*Цены:*
• Минимальная: *{min_price:.0f}₽*
• Максимальная: *{max_price:.0f}₽*
• Средняя: *{avg_price:.0f}₽*

*Топ-5 категорий:*
        """

        for cat in top_categories:
            percentage = (cat['count'] / total_products) * 100 if total_products > 0 else 0
            response += f"\n• {cat['name']}: {cat['count']} ({percentage:.1f}%)"

        response += f"\n\n⭐ *Топ-5 товаров по рейтингу:*"
        for product in top_rated:
            response += f"\n• {product['name']} - {product['price']:.0f}₽ ({'⭐' * int(product['rating'])}{'½' if product['rating'] % 1 >= 0.5 else ''})"

        response += f"\n\n🌐 *Web App:*\n`{WEB_APP_URL}`"

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении статистики.")


@bot.message_handler(commands=['search', 'поиск'])
def search_command(message):
    """Команда поиска товаров"""
    msg = bot.send_message(
        message.chat.id,
        "🔍 *Введите название товара или бренда для поиска:*",
        parse_mode='Markdown'
    )
    bot.register_next_step_handler(msg, search_products)


@bot.message_handler(commands=['cart', 'корзина'])
def cart_command(message):
    """Показать корзину"""
    show_cart(message)


@bot.message_handler(commands=['orders', 'заказы'])
def orders_command(message):
    """Показать заказы пользователя"""
    show_user_orders(message)


# ========== ОБРАБОТКА WEB APP DATA ==========

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    """Обработка данных из Web App"""
    logger.info(f"Получены данные от Web App от пользователя {message.from_user.id}")

    try:
        # Парсим JSON данные
        web_app_data = json.loads(message.web_app_data.data)
        logger.info(f"Данные Web App: {web_app_data}")

        action = web_app_data.get('action')

        if action == 'get_products_by_category':
            category_slug = web_app_data.get('category')
            send_products_by_category(message.chat.id, category_slug)

        elif action == 'get_product_details':
            product_id = web_app_data.get('product_id')
            send_product_details(message.chat.id, product_id)

        elif action == 'add_to_cart':
            product_id = web_app_data.get('product_id')
            add_to_cart_web(message.chat.id, product_id)

        elif action == 'place_order':
            cart_items = web_app_data.get('cart', [])
            place_order_web(message.chat.id, cart_items, message.from_user)

        elif action == 'test':
            bot.send_message(
                message.chat.id,
                f"✅ Получены тестовые данные: {web_app_data.get('message', 'No message')}"
            )

        else:
            # Для простых текстовых данных (название категории)
            send_products_by_category(message.chat.id, message.web_app_data.data)

    except json.JSONDecodeError:
        # Для обратной совместимости с простым текстом
        logger.info("Получены простые текстовые данные от Web App")
        send_products_by_category(message.chat.id, message.web_app_data.data)

    except Exception as e:
        logger.error(f"Ошибка обработки Web App данных: {e}")
        bot.send_message(
            message.chat.id,
            "❌ Ошибка обработки запроса. Попробуйте еще раз."
        )


def send_products_by_category(chat_id, category_slug):
    """Отправка товаров по категории"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Получаем информацию о категории
        cursor.execute("SELECT name, description FROM categories WHERE slug = ?", (category_slug,))
        category = cursor.fetchone()

        if not category:
            bot.send_message(chat_id, f"❌ Категория '{category_slug}' не найдена.")
            conn.close()
            return

        # Получаем товары этой категории
        cursor.execute("""
            SELECT p.id, p.name, p.price, p.brand, p.in_stock, p.rating, p.image_url
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.slug = ? 
            ORDER BY p.rating DESC, p.price
            LIMIT 15
        """, (category_slug,))

        products = cursor.fetchall()
        conn.close()

        if products:
            response = f"📦 *Товары категории '{category['name']}':*\n"
            response += f"{category['description']}\n\n"

            for i, product in enumerate(products, 1):
                stock_status = "✅ В наличии" if product['in_stock'] else "⏳ Под заказ"

                # Формируем звездный рейтинг
                rating = product['rating']
                stars = ""
                if rating and rating > 0:
                    full_stars = int(rating)
                    half_star = rating - full_stars >= 0.5
                    stars = "⭐" * full_stars
                    if half_star:
                        stars += "½"
                    rating_text = f" | {stars}"
                else:
                    rating_text = ""

                response += f"*{i}. {product['name']}*\n"
                response += f"   🏷️ {product['brand']}\n"
                response += f"   💰 {product['price']:.0f}₽\n"
                response += f"   📊 {stock_status}{rating_text}\n\n"

            response += f"*Всего найдено: {len(products)} товаров*\n"
            response += "*Используйте /search для поиска других товаров*"

        else:
            response = f"❌ В категории '{category['name']}' товаров не найдено.\n"
            response += "Попробуйте другую категорию или используйте поиск."

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при получении товаров по категории: {e}")
        bot.send_message(chat_id, f"❌ Ошибка при получении товаров: {str(e)[:100]}")


def send_product_details(chat_id, product_id):
    """Отправка детальной информации о товаре"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """, (product_id,))

        product = cursor.fetchone()
        conn.close()

        if not product:
            bot.send_message(chat_id, "❌ Товар не найден.")
            return

        # Формируем детальное описание
        stock_status = "✅ В наличии" if product['in_stock'] else "⏳ Под заказ (3-5 дней)"

        # Формируем звездный рейтинг
        rating = product['rating']
        stars = ""
        if rating and rating > 0:
            full_stars = int(rating)
            half_star = rating - full_stars >= 0.5
            stars = "⭐" * full_stars
            if half_star:
                stars += "½"
            rating_text = f"\n⭐ Рейтинг: {stars} ({rating}/5)"
        else:
            rating_text = ""

        response = f"""
*{product['name']}*

🏷️ *Бренд:* {product['brand']}
📂 *Категория:* {product['category_name']}
💰 *Цена:* {product['price']:.0f}₽
📊 *Наличие:* {stock_status}
{rating_text}

📝 *Описание:*
{product['description']}

⚙️ *Характеристики:*
{product['specs']}

💡 *Совет:* Используйте Web App для удобного оформления заказа!
        """

        # Если есть изображение, отправляем его с подписью
        if product['image_url'] and product['image_url'].startswith('http'):
            try:
                bot.send_photo(
                    chat_id,
                    product['image_url'],
                    caption=response,
                    parse_mode='Markdown'
                )
            except:
                bot.send_message(chat_id, response, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при получении деталей товара: {e}")
        bot.send_message(chat_id, "❌ Ошибка при получении информации о товаре.")


def add_to_cart_web(chat_id, product_id):
    """Добавление товара в корзину через Web App"""
    try:
        # В реальном приложении здесь была бы логика добавления в БД
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name, price FROM products WHERE id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()

        if product:
            response = f"✅ Товар добавлен в корзину:\n"
            response += f"• {product['name']}\n"
            response += f"• Цена: {product['price']:.0f}₽\n\n"
            response += "🛒 Перейдите в раздел «Корзина» для оформления заказа."
        else:
            response = "❌ Товар не найден."

        bot.send_message(chat_id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при добавлении в корзину: {e}")
        bot.send_message(chat_id, "❌ Ошибка при добавлении товара в корзину.")


def place_order_web(chat_id, cart_items, user):
    """Оформление заказа через Web App"""
    try:
        if not cart_items:
            bot.send_message(chat_id, "❌ Корзина пуста!")
            return

        # В реальном приложении здесь была бы логика создания заказа в БД
        conn = get_db_connection()
        cursor = conn.cursor()

        total_price = 0
        products_list = []

        for item in cart_items:
            cursor.execute("SELECT name, price FROM products WHERE id = ?", (item['id'],))
            product = cursor.fetchone()
            if product:
                quantity = item.get('quantity', 1)
                total_price += product['price'] * quantity
                products_list.append(f"{product['name']} x{quantity}")

        # Сохраняем заказ в БД
        cursor.execute("""
            INSERT INTO orders (user_id, user_name, products, total_price, status)
            VALUES (?, ?, ?, ?, ?)
        """, (user.id, user.first_name, ', '.join(products_list), total_price, 'pending'))

        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        response = f"""
✅ *Заказ #{order_id} успешно оформлен!*

👤 *Покупатель:* {user.first_name} (@{user.username or 'нет'})
📦 *Товары:*
"""
        for product in products_list:
            response += f"• {product}\n"

        response += f"\n💰 *Итого:* {total_price:.0f}₽\n"
        response += "📊 *Статус:* Ожидает обработки\n\n"
        response += "📞 Наш менеджер свяжется с вами в течение 30 минут для подтверждения заказа."

        bot.send_message(chat_id, response, parse_mode='Markdown')

        # Здесь можно добавить уведомление администратору

    except Exception as e:
        logger.error(f"Ошибка при оформлении заказа: {e}")
        bot.send_message(chat_id, "❌ Ошибка при оформлении заказа. Попробуйте еще раз.")


# ========== ОБРАБОТКА ТЕКСТОВЫХ СООБЩЕНИЙ ==========

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    """Обработка всех текстовых сообщений"""

    if message.text == '📁 Категории товаров':
        show_all_categories(message)

    elif message.text == '🔍 Поиск товаров':
        search_command(message)

    elif message.text == '🛍️ Корзина':
        show_cart(message)

    elif message.text == '📋 Мои заказы':
        show_user_orders(message)

    elif message.text == '📊 Статистика':
        stats_command(message)

    elif message.text == '🆘 Помощь':
        help_command(message)

    elif message.text.lower() in ['привет', 'hello', 'hi']:
        bot.send_message(
            message.chat.id,
            f"Привет, {message.from_user.first_name}! 👋\n"
            "Добро пожаловать в магазин компьютерных комплектующих!\n"
            "Используйте /start для главного меню."
        )

    else:
        bot.send_message(
            message.chat.id,
            "🤔 Я не понял команду.\n\n"
            "Используйте кнопки меню или команды:\n"
            "/start - главное меню\n"
            "/help - справка\n"
            "/web - открыть Web App\n"
            "/categories - все категории\n"
            "/search - поиск товаров"
        )


def show_all_categories(message):
    """Показать все категории"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name, description, icon FROM categories ORDER BY name")
        categories = cursor.fetchall()

        conn.close()

        response = "📁 *Доступные категории товаров:*\n\n"

        for category in categories:
            response += f"• {category['icon']} *{category['name']}* - {category['description']}\n"

        response += "\n🛒 *Совет:* Для удобного выбора категории с иконками используйте Web App!\n"
        response += "Нажмите «🛒 Открыть каталог товаров»"

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при получении категорий: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении категорий.")


def search_products(message):
    """Поиск товаров"""
    search_query = message.text.strip()

    if not search_query:
        bot.send_message(message.chat.id, "❌ Введите запрос для поиска.")
        return

    if len(search_query) < 2:
        bot.send_message(message.chat.id, "❌ Слишком короткий запрос. Введите минимум 2 символа.")
        return

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.name, p.brand, p.price, p.in_stock, p.rating, c.name as category
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.name LIKE ? OR p.brand LIKE ? OR p.description LIKE ?
            ORDER BY p.rating DESC, p.price
            LIMIT 15
        """, (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))

        products = cursor.fetchall()
        conn.close()

        if products:
            response = f"🔍 *Результаты поиска: '{search_query}'*\n\n"

            for i, product in enumerate(products, 1):
                stock_status = "✅" if product['in_stock'] else "⏳"

                # Формируем звездный рейтинг
                rating = product['rating']
                stars = ""
                if rating and rating > 0:
                    full_stars = int(rating)
                    stars = "⭐" * full_stars
                    if rating - full_stars >= 0.5:
                        stars += "½"

                response += f"*{i}. {product['name']}*\n"
                response += f"   🏷️ {product['brand']}\n"
                response += f"   📂 {product['category']}\n"
                response += f"   💰 {product['price']:.0f}₽\n"
                response += f"   📊 {stock_status}"
                if stars:
                    response += f" | {stars}\n\n"
                else:
                    response += "\n\n"

            response += f"*Найдено: {len(products)} товаров*\n"
            response += "*Для более точного поиска используйте полное название товара*"

        else:
            response = f"❌ По запросу '{search_query}' ничего не найдено.\n"
            response += "Попробуйте:\n"
            response += "• Использовать другое название\n"
            response += "• Проверить орфографию\n"
            response += "• Использовать Web App для выбора по категориям"

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при поиске товаров: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при поиске.")


def show_cart(message):
    """Показать корзину (упрощенная версия)"""
    response = """
🛒 *Ваша корзина*

В текущей версии корзина работает через Web App интерфейс.

*Для работы с корзиной:*
1. Нажмите «🛒 Открыть каталог товаров»
2. Выберите товары в Web App интерфейсе
3. Добавьте товары в корзину
4. Оформите заказ

*Преимущества Web App:*
• Удобный интерфейс
• Быстрый выбор товаров
• Автоматический расчет суммы
• Простое оформление заказа

🖱️ *Нажмите кнопку ниже, чтобы открыть каталог:*
    """

    web_app = types.WebAppInfo(url=WEB_APP_URL)

    keyboard = types.InlineKeyboardMarkup()
    web_btn = types.InlineKeyboardButton(
        text="🛒 Открыть каталог товаров",
        web_app=web_app
    )
    keyboard.add(web_btn)

    bot.send_message(
        message.chat.id,
        response,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


def show_user_orders(message):
    """Показать заказы пользователя"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, products, total_price, status, created_at 
            FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (message.from_user.id,))

        orders = cursor.fetchall()
        conn.close()

        if orders:
            response = f"📋 *Ваши последние заказы:*\n\n"

            for order in orders:
                status_icons = {
                    'pending': '⏳',
                    'processing': '⚙️',
                    'shipped': '🚚',
                    'delivered': '✅',
                    'cancelled': '❌'
                }
                status_icon = status_icons.get(order['status'], '📋')

                # Форматируем дату
                created_at = order['created_at']
                if 'T' in str(created_at):
                    created_at = str(created_at).split('T')[0]

                response += f"*Заказ #{order['id']}* {status_icon}\n"
                response += f"📦 *Товары:* {order['products'][:50]}...\n"
                response += f"💰 *Сумма:* {order['total_price']:.0f}₽\n"
                response += f"📊 *Статус:* {order['status'].capitalize()}\n"
                response += f"📅 *Дата:* {created_at}\n\n"

            response += "📞 *Контакты поддержки:* @tech_support_bot"

        else:
            response = "📋 *У вас пока нет заказов.*\n\n"
            response += "Сделайте свой первый заказ через Web App интерфейс!\n"
            response += "Нажмите «🛒 Открыть каталог товаров»"

        bot.send_message(message.chat.id, response, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Ошибка при получении заказов: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при получении заказов.")


# ========== ЗАПУСК БОТА ==========

if __name__ == '__main__':
    print("=" * 50)
    print("🖥️  МАГАЗИН КОМПЬЮТЕРНЫХ КОМПЛЕКТУЮЩИХ С WEB APP")
    print("=" * 50)

    # Проверка токена
    if 'ВАШ_ТОКЕН_БОТА' in TOKEN or len(TOKEN) < 30:
        print("❌ ОШИБКА: Не указан токен бота!")
        print("ℹ️  Получите токен у @BotFather в Telegram")
        print("ℹ️  Замените 'ВАШ_ТОКЕН_БОТА' на свой токен в строке 13")
        exit(1)

    # Инициализация базы данных
    if not os.path.exists(DB_PATH):
        print("📁 Создание новой базы данных...")
        init_database()
    else:
        print("📁 База данных уже существует.")

    # Проверка базы данных
    check_database()

    print(f"🌐 Web App URL: {WEB_APP_URL}")
    print("=" * 50)
    print("\n✅ Бот запущен и готов к работе!")
    print("📱 Откройте Telegram и найдите вашего бота")
    print("⚡ Используйте /start для начала работы")
    print("🛒 Для полного функционала используйте Web App интерфейс")
    print("ℹ️  Используйте Ctrl+C для остановки\n")

    try:
        bot.polling(none_stop=True, interval=0, timeout=30)
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        print(f"❌ Критическая ошибка: {e}")