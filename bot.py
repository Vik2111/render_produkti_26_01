import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Включаем логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_USERS = {501851181}  # ID членов семьи

PRODUCT_CATEGORIES = {
    "Хлібні вироби": ["Хліб", "Лаваш", "Багет", "Чіабата", "Круасани", "Слойки"],
    "Соління": ["Капуста кв.", "Морквичка", "Огірок", "Помідор"],
    "М’ясо": {
        "Свинина": ["Вирізка", "Ребра", "Фарш"],
        "Курятина": ["Філе", "Крила", "Гомілка", "Шлунки"],
        "Яловичина": ["Стейк", "Фарш.", "Ребра."],
        "Індичатина": ["Філе.", "Гуляш", "Гомілка."],
        "Сало": ["Солоне", "Копчене"]},
    "Риба": ["Свіжа риба", "Сьомга", "Форель", "Оселедець", "Ікра"],
    "Овочі": ["Огірки", "Помідори", "Картопля", "Цибуля", "Морква", "Капуста", "Перець", "Буряк", "Часник", "Баклажани", "Кабачки", "Гриби"],
    "Зелень": ["Цибулька", "Петрушка", "Кріп", "Салат", "Щавель", "Редиска"],
    "Фрукти": ["Лимон", "Яблука", "Груші", "Виноград", "Слива"],
    "Молочні та яйця": ["Яйця", "Сир", "Творог", "Молоко", "Сметана", "Масло","Гералакт", "Вершки"],
    "Бакалія": ["Макарони", "Крупа гречана", "Борошно", "Цукор", "Сіль"],
    "Чай, кава": ["Чай", "Кава"],
    "Ковбасні та Сир": ["Варена", "Копчена", "Сосиски", "Сир твердий", "Мацарелла", "Сулугуні", "Сыр м’який"],
    "Соуси, приправи": ["Олія рослинна", "Олія домашня", "Оцет", "Оливки", "Маслини", "Майонез", "Соев. соус", "Соуси інші", "Приправи та спеції"],
    "Консервація": ["Варення та джеми", "Фрукти", "Гриби", "Риба", "М’ясо", "Овочі", "Паштет"],
    "Заморожені продукти": ["Тісто", "Морозиво", "Пельмені", "Вареники", "Млинці"],    
"Туалет та Ванна": ["Папір", "Каченя", "Міло", "Шампунь", "Палички", "резерв", "резерв2", "резерв3"],    
"Кухня": ["Серветки", "Бум. рушник", "Ганчірки", "резерв4", "резерв5"],

 }

selected_products = {}


def is_authorized(user_id):
    return user_id in ALLOWED_USERS


async def show_categories(update: Update, context: CallbackContext):
    categories = list(PRODUCT_CATEGORIES.keys())
    keyboard = [
        [InlineKeyboardButton(categories[i], callback_data=f"category_{categories[i]}"),
         InlineKeyboardButton(categories[i + 1], callback_data=f"category_{categories[i + 1]}")]
        for i in range(0, len(categories) - 1, 2)
    ]
    if len(categories) % 2 == 1:
        keyboard.append([InlineKeyboardButton(categories[-1], callback_data=f"category_{categories[-1]}")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text("🛍 Оберіть категорію:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("🛍 Оберіть категорію:", reply_markup=reply_markup)


async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return

    selected_products[user_id] = set()
    await show_categories(update, context)


async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = update.effective_user.id
    await query.answer()

    if not is_authorized(user_id):
        await query.message.reply_text("❌ У вас нет доступа к этому боту.")
        return

    data = query.data

    if data.startswith("category_"):
        category = data.split("_", 1)[1]
        if isinstance(PRODUCT_CATEGORIES[category], dict):
            await show_subcategories(update, user_id, category, query)
        else:
            await show_products(update, user_id, category, query)

    elif data.startswith("subcategory_"):
        subcategory = data.split("_", 1)[1]
        category = next((cat for cat, subcats in PRODUCT_CATEGORIES.items() if subcategory in subcats), None)
        if category:
            await show_products(update, user_id, category, query, subcategory)

    elif data.startswith("select_"):
        product = data.split("_", 1)[1]

        if user_id not in selected_products:
            selected_products[user_id] = set()

        if product in selected_products[user_id]:
            selected_products[user_id].remove(product)
        else:
            selected_products[user_id].add(product)

        category = next((cat for cat, items in PRODUCT_CATEGORIES.items() if isinstance(items, list) and product in items), None)
        if not category:
            category = next((cat for cat, subcats in PRODUCT_CATEGORIES.items() if isinstance(subcats, dict) and any(product in subitems for subitems in subcats.values())), None)
        if category:
            if isinstance(PRODUCT_CATEGORIES[category], dict):
                subcategory = next((subcat for subcat, items in PRODUCT_CATEGORIES[category].items() if product in items), None)
                if subcategory:
                    await show_products(update, user_id, category, query, subcategory)
            else:
                await show_products(update, user_id, category, query)

    elif data == "back_to_categories":
        await show_categories(update, context)

    elif data.startswith("back_to_"):
        category = data.split("_", 2)[2]
        await show_subcategories(update, user_id, category, query)

    elif data == "done":
        await send_shopping_list(update, context, user_id)


async def show_subcategories(update: Update, user_id: int, category: str, query=None):
    subcategories = list(PRODUCT_CATEGORIES[category].keys())
    keyboard = [
        [InlineKeyboardButton(subcategories[i], callback_data=f"subcategory_{subcategories[i]}"),
         InlineKeyboardButton(subcategories[i + 1], callback_data=f"subcategory_{subcategories[i + 1]}")]
        for i in range(0, len(subcategories) - 1, 2)
    ]
    if len(subcategories) % 2 == 1:
        keyboard.append([InlineKeyboardButton(subcategories[-1], callback_data=f"subcategory_{subcategories[-1]}")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_categories")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"📌 Ви обрали категорію: *{category}*\nВиберіть підкатегорію:"
    if query:
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)


async def show_products(update: Update, user_id: int, category: str, query=None, subcategory=None):
    if subcategory:
        products = PRODUCT_CATEGORIES[category].get(subcategory, [])
        back_callback_data = f"back_to_{category}"
        text = f"📌 Ви обрали підкатегорію: *{subcategory}* з категорії *{category}*\nВиберіть продукти:"
    else:
        products = PRODUCT_CATEGORIES.get(category, [])
        back_callback_data = "back_to_categories"
        text = f"📌 Ви обрали категорію: *{category}*\nВиберіть продукти:"
    
    keyboard = [
        [InlineKeyboardButton(f"{'✅ ' if product in selected_products.get(user_id, set()) else ''}{product}",
                              callback_data=f"select_{product}")] for product in products
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=back_callback_data)])
    keyboard.append([InlineKeyboardButton("✅ Готово", callback_data="done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        await query.edit_message_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text=text, parse_mode="Markdown", reply_markup=reply_markup)


async def send_shopping_list(update: Update, context: CallbackContext, user_id: int):
    if not selected_products.get(user_id):
        await update.callback_query.edit_message_text("❌ Ви не обрали жодного продукту.")
        return

    sorted_list = {category: [p for p in items if p in selected_products[user_id]]
                   for category, items in PRODUCT_CATEGORIES.items()
                   if isinstance(items, list) and any(p in selected_products[user_id] for p in items)}

    for category, subcats in PRODUCT_CATEGORIES.items():
        if isinstance(subcats, dict):
            sorted_sublist = {subcat: [p for p in items if p in selected_products[user_id]]
                              for subcat, items in subcats.items()
                              if any(p in selected_products[user_id] for p in items)}
            if sorted_sublist:
                if category not in sorted_list:
                    sorted_list[category] = {}
                sorted_list[category].update(sorted_sublist)

    message_text = "🛒 *Список покупок:*\n\n"
    for category, items in sorted_list.items():
        if isinstance(items, dict):
            message_text += f"*{category}:*\n"
            for subcat, subitems in items.items():
                message_text += f"  *{subcat}:*\n"
                message_text += "\n".join(f"  • {product}" for product in subitems) + "\n\n"
        else:
            message_text += f"*{category}:*\n"
            message_text += "\n".join(f"• {product}" for product in items) + "\n\n"

    for family_member in ALLOWED_USERS:
        try:
            await context.bot.send_message(chat_id=family_member, text=message_text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {family_member}: {e}")

    await update.callback_query.edit_message_text("✅ Список покупок оновлений та надісланий всім членам сім'ї!")
    selected_products[user_id] = set()


async def clear_list(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return

    selected_products[user_id] = set()
    await update.message.reply_text("🗑 Список покупок очищений!")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_list))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()

