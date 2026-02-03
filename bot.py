"""
Telegram Shopping List Bot
Бот для составления списка покупок с категориями и подкатегориями
"""

import os
import logging
from typing import Set, Dict, Union, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext
)

# ============================================================================
# CONFIGURATION / КОНФИГУРАЦИЯ
# ============================================================================

# Telegram Bot Token из переменной окружения
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

# ID разрешенных пользователей (члены семьи)
ALLOWED_USERS = {501851181}

# Категории продуктов
PRODUCT_CATEGORIES: Dict[str, Union[list, dict]] = {
    "Хлібні вироби": [
        "Хліб", "Лаваш", "Багет", "Чіабата", "Круасани", "Слойки"
    ],
    "Соління": [
        "Капуста кв.", "Морквичка", "Огірок", "Помідор"
    ],
    "М'ясо": {
        "Свинина": ["Вирізка", "Ребра", "Фарш"],
        "Курятина": ["Філе", "Крила", "Гомілка", "Шлунки"],
        "Яловичина": ["Стейк", "Фарш.", "Ребра."],
        "Індичатина": ["Філе.", "Гуляш", "Гомілка."],
        "Сало": ["Солоне", "Копчене"]
    },
    "Риба": [
        "Свіжа риба", "Сьомга", "Форель", "Оселедець", "Ікра"
    ],
    "Овочі": [
        "Огірки", "Помідори", "Картопля", "Цибуля", "Морква",
        "Капуста", "Перець", "Буряк", "Часник", "Баклажани",
        "Кабачки", "Гриби"
    ],
    "Зелень": [
        "Цибулька", "Петрушка", "Кріп", "Салат", "Щавель", "Редиска"
    ],
    "Фрукти": [
        "Лимон", "Яблука", "Груші", "Виноград", "Слива"
    ],
    "Молочні та яйця": [
        "Яйця", "Сир", "Творог", "Молоко", "Сметана",
        "Масло", "Гералакт", "Вершки"
    ],
    "Бакалія": [
        "Макарони", "Крупа гречана", "Борошно", "Цукор", "Сіль"
    ],
    "Чай, кава": ["Чай", "Кава"],
    "Ковбасні та Сир": [
        "Варена", "Копчена", "Сосиски", "Сир твердий",
        "Мацарелла", "Сулугуні", "Сыр м'який"
    ],
    "Соуси, приправи": [
        "Олія рослинна", "Олія домашня", "Оцет", "Оливки",
        "Маслини", "Майонез", "Соев. соус", "Соуси інші",
        "Приправи та спеції"
    ],
    "Консервація": [
        "Варення та джеми", "Фрукти", "Гриби", "Риба",
        "М'ясо", "Овочі", "Паштет"
    ],
    "Заморожені продукти": [
        "Тісто", "Морозиво", "Пельмені", "Вареники", "Млинці"
    ],
    "Туалет та Ванна": [
        "Папір", "Каченя", "Міло", "Шампунь", "Палички",
        "резерв", "резерв2", "резерв3"
    ],
    "Кухня": [
        "Серветки", "Бум. рушник", "Ганчірки",
        "резерв4", "резерв5"
    ],
}

# ============================================================================
# LOGGING SETUP / НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================================
# STATE MANAGEMENT / УПРАВЛЕНИЕ СОСТОЯНИЕМ
# ============================================================================

# Словарь для хранения выбранных продуктов для каждого пользователя
selected_products: Dict[int, Set[str]] = {}


# ============================================================================
# UTILITY FUNCTIONS / ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def is_authorized(user_id: int) -> bool:
    """Проверяет, авторизован ли пользователь"""
    return user_id in ALLOWED_USERS


def get_user_selected_products(user_id: int) -> Set[str]:
    """Возвращает набор выбранных продуктов для пользователя"""
    if user_id not in selected_products:
        selected_products[user_id] = set()
    return selected_products[user_id]


# ============================================================================
# CATEGORY DISPLAY / ОТОБРАЖЕНИЕ КАТЕГОРИЙ
# ============================================================================

async def show_categories(update: Update, context: CallbackContext) -> None:
    """Отображает главное меню с категориями продуктов"""
    categories = list(PRODUCT_CATEGORIES.keys())
    
    # Создаем клавиатуру с двумя кнопками в ряд
    keyboard = []
    for i in range(0, len(categories) - 1, 2):
        keyboard.append([
            InlineKeyboardButton(
                categories[i],
                callback_data=f"category_{categories[i]}"
            ),
            InlineKeyboardButton(
                categories[i + 1],
                callback_data=f"category_{categories[i + 1]}"
            )
        ])
    
    # Добавляем последнюю категорию, если их нечетное количество
    if len(categories) % 2 == 1:
        keyboard.append([
            InlineKeyboardButton(
                categories[-1],
                callback_data=f"category_{categories[-1]}"
            )
        ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем или редактируем сообщение
    if update.callback_query:
        await update.callback_query.edit_message_text(
            "🛍 Оберіть категорію:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "🛍 Оберіть категорію:",
            reply_markup=reply_markup
        )


async def show_subcategories(
    update: Update,
    user_id: int,
    category: str,
    query: Optional[Update] = None
) -> None:
    """Отображает подкатегории для выбранной категории"""
    subcategories = list(PRODUCT_CATEGORIES[category].keys())
    
    # Создаем клавиатуру с подкатегориями
    keyboard = []
    for i in range(0, len(subcategories) - 1, 2):
        keyboard.append([
            InlineKeyboardButton(
                subcategories[i],
                callback_data=f"subcategory_{subcategories[i]}"
            ),
            InlineKeyboardButton(
                subcategories[i + 1],
                callback_data=f"subcategory_{subcategories[i + 1]}"
            )
        ])
    
    if len(subcategories) % 2 == 1:
        keyboard.append([
            InlineKeyboardButton(
                subcategories[-1],
                callback_data=f"subcategory_{subcategories[-1]}"
            )
        ])
    
    # Кнопка "Назад"
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data="back_to_categories")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"📌 Ви обрали категорію: *{category}*\nВиберіть підкатегорію:"
    
    if query:
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


async def show_products(
    update: Update,
    user_id: int,
    category: str,
    query: Optional[Update] = None,
    subcategory: Optional[str] = None
) -> None:
    """Отображает список продуктов для выбора"""
    # Определяем список продуктов и текст заголовка
    if subcategory:
        products = PRODUCT_CATEGORIES[category].get(subcategory, [])
        back_callback_data = f"back_to_{category}"
        text = (
            f"📌 Ви обрали підкатегорію: *{subcategory}* "
            f"з категорії *{category}*\nВиберіть продукти:"
        )
    else:
        products = PRODUCT_CATEGORIES.get(category, [])
        back_callback_data = "back_to_categories"
        text = f"📌 Ви обрали категорію: *{category}*\nВиберіть продукти:"
    
    user_products = get_user_selected_products(user_id)
    
    # Создаем кнопки для каждого продукта
    keyboard = []
    for product in products:
        # Добавляем галочку, если продукт уже выбран
        button_text = f"{'✅ ' if product in user_products else ''}{product}"
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"select_{product}"
            )
        ])
    
    # Кнопки навигации
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data=back_callback_data)
    ])
    keyboard.append([
        InlineKeyboardButton("✅ Готово", callback_data="done")
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )


# ============================================================================
# COMMAND HANDLERS / ОБРАБОТЧИКИ КОМАНД
# ============================================================================

async def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    # Инициализируем пустой список для пользователя
    selected_products[user_id] = set()
    
    logger.info(f"User {user_id} started the bot")
    await show_categories(update, context)


async def clear_list(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /clear - очищает список покупок"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    selected_products[user_id] = set()
    logger.info(f"User {user_id} cleared shopping list")
    await update.message.reply_text("🗑 Список покупок очищений!")


# ============================================================================
# CALLBACK HANDLERS / ОБРАБОТЧИКИ CALLBACK-ЗАПРОСОВ
# ============================================================================

async def button_handler(update: Update, context: CallbackContext) -> None:
    """Главный обработчик всех нажатий на inline-кнопки"""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    if not is_authorized(user_id):
        await query.message.reply_text("❌ У вас нет доступа к этому боту.")
        return
    
    data = query.data
    
    # Обработка выбора категории
    if data.startswith("category_"):
        category = data.split("_", 1)[1]
        
        if isinstance(PRODUCT_CATEGORIES[category], dict):
            # Категория с подкатегориями
            await show_subcategories(update, user_id, category, query)
        else:
            # Категория без подкатегорий
            await show_products(update, user_id, category, query)
    
    # Обработка выбора подкатегории
    elif data.startswith("subcategory_"):
        subcategory = data.split("_", 1)[1]
        
        # Находим родительскую категорию
        category = next(
            (cat for cat, subcats in PRODUCT_CATEGORIES.items()
             if isinstance(subcats, dict) and subcategory in subcats),
            None
        )
        
        if category:
            await show_products(update, user_id, category, query, subcategory)
    
    # Обработка выбора/снятия продукта
    elif data.startswith("select_"):
        product = data.split("_", 1)[1]
        user_products = get_user_selected_products(user_id)
        
        # Переключаем состояние продукта (выбран/не выбран)
        if product in user_products:
            user_products.remove(product)
            logger.info(f"User {user_id} deselected: {product}")
        else:
            user_products.add(product)
            logger.info(f"User {user_id} selected: {product}")
        
        # Находим категорию продукта для обновления экрана
        category = None
        subcategory = None
        
        # Ищем в простых категориях
        for cat, items in PRODUCT_CATEGORIES.items():
            if isinstance(items, list) and product in items:
                category = cat
                break
        
        # Ищем в категориях с подкатегориями
        if not category:
            for cat, subcats in PRODUCT_CATEGORIES.items():
                if isinstance(subcats, dict):
                    for subcat, items in subcats.items():
                        if product in items:
                            category = cat
                            subcategory = subcat
                            break
                    if category:
                        break
        
        # Обновляем экран с продуктами
        if category:
            await show_products(update, user_id, category, query, subcategory)
    
    # Возврат к главному меню категорий
    elif data == "back_to_categories":
        await show_categories(update, context)
    
    # Возврат к подкатегориям
    elif data.startswith("back_to_"):
        category = data.split("_", 2)[2]
        await show_subcategories(update, user_id, category, query)
    
    # Завершение выбора и отправка списка
    elif data == "done":
        await send_shopping_list(update, context, user_id)


# ============================================================================
# SHOPPING LIST GENERATION / ФОРМИРОВАНИЕ СПИСКА ПОКУПОК
# ============================================================================

async def send_shopping_list(
    update: Update,
    context: CallbackContext,
    user_id: int
) -> None:
    """Формирует и отправляет список покупок всем членам семьи"""
    user_products = get_user_selected_products(user_id)
    
    if not user_products:
        await update.callback_query.edit_message_text(
            "❌ Ви не обрали жодного продукту."
        )
        return
    
    # Сортируем продукты по категориям
    sorted_list = {}
    
    # Обрабатываем простые категории (списки)
    for category, items in PRODUCT_CATEGORIES.items():
        if isinstance(items, list):
            selected_in_category = [p for p in items if p in user_products]
            if selected_in_category:
                sorted_list[category] = selected_in_category
    
    # Обрабатываем категории с подкатегориями (словари)
    for category, subcats in PRODUCT_CATEGORIES.items():
        if isinstance(subcats, dict):
            sorted_sublist = {}
            
            for subcat, items in subcats.items():
                selected_in_subcat = [p for p in items if p in user_products]
                if selected_in_subcat:
                    sorted_sublist[subcat] = selected_in_subcat
            
            if sorted_sublist:
                sorted_list[category] = sorted_sublist
    
    # Формируем текст сообщения
    message_text = "🛒 *Список покупок:*\n\n"
    
    for category, items in sorted_list.items():
        if isinstance(items, dict):
            # Категория с подкатегориями
            message_text += f"*{category}:*\n"
            for subcat, subitems in items.items():
                message_text += f"  *{subcat}:*\n"
                message_text += "\n".join(f"    • {product}" for product in subitems)
                message_text += "\n\n"
        else:
            # Простая категория
            message_text += f"*{category}:*\n"
            message_text += "\n".join(f"  • {product}" for product in items)
            message_text += "\n\n"
    
    # Отправляем список всем членам семьи
    success_count = 0
    for family_member in ALLOWED_USERS:
        try:
            await context.bot.send_message(
                chat_id=family_member,
                text=message_text,
                parse_mode="Markdown"
            )
            success_count += 1
            logger.info(f"Shopping list sent to user {family_member}")
        except Exception as e:
            logger.error(
                f"Failed to send shopping list to user {family_member}: {e}"
            )
    
    # Подтверждаем отправку
    await update.callback_query.edit_message_text(
        f"✅ Список покупок оновлений та надісланий "
        f"{success_count} членам сім'ї!"
    )
    
    # Очищаем список после отправки
    selected_products[user_id] = set()
    logger.info(f"User {user_id} completed shopping list with {len(user_products)} items")


# ============================================================================
# MAIN APPLICATION / ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================

def main() -> None:
    """Основная функция запуска бота в режиме webhook на Render"""
    try:
        # Создаем приложение
        app = Application.builder().token(TOKEN).build()

        # Регистрируем обработчики команд
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("clear", clear_list))

        # Регистрируем обработчик callback-кнопок
        app.add_handler(CallbackQueryHandler(button_handler))

        logger.info("=" * 50)
        logger.info("Shopping List Bot started successfully (webhook mode)!")
        logger.info(f"Authorized users: {ALLOWED_USERS}")
        logger.info(f"Categories loaded: {len(PRODUCT_CATEGORIES)}")
        logger.info("=" * 50)

        # ------------------------------------------------------------------
        # НАСТРОЙКИ ДЛЯ RENDER
        # ------------------------------------------------------------------
        # Render даёт URL сервиса в переменной окружения
        render_url = os.getenv("RENDER_EXTERNAL_URL")
        if not render_url:
            raise RuntimeError("RENDER_EXTERNAL_URL is not set")

        # Порт, к которому нужно привязаться (Render ожидает, что мы слушаем PORT)
        port = int(os.getenv("PORT", "10000"))

        # Путь webhook'а (можешь поменять на любой)
        webhook_path = "/webhook"

        # Полный URL, который Telegram будет вызывать
        webhook_url = f"{render_url}{webhook_path}"

        logger.info(f"Using webhook URL: {webhook_url} on port {port}")

        # Настраиваем webhook
        async def run():
            # Сбрасываем старый webhook и ставим новый
            await app.bot.delete_webhook()
            await app.bot.set_webhook(url=webhook_url)

            # Запускаем встроенный веб‑сервер PTB, который слушает PORT
            await app.run_webhook(
                listen="0.0.0.0",
                port=port,
                url_path=webhook_path,
                webhook_url=webhook_url,
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
            )

        # Запускаем асинхронный цикл
        import asyncio
        asyncio.run(run())

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise


# ============================================================================
# ENTRY POINT / ТОЧКА ВХОДА
# ============================================================================

if __name__ == "__main__":
    main()

