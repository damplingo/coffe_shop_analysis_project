import os
import psycopg2
import random
from datetime import date, timedelta, time

db_connection = psycopg2.connect(
    host="localhost",
    database="urban_coffee",
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

cur = db_connection.cursor()
cur.execute("TRUNCATE fact_orders_item, fact_orders, dim_product, dim_cafe, dim_date RESTART IDENTITY CASCADE;")
#заполнение dim_date
HOLIDAYS = {
    date(2024, 1, 1): "Новый год",
    date(2024, 1, 2): "Новогодние каникулы",
    date(2024, 1, 7): "Рождество",
    date(2024, 2, 23): "День защитника Отечества",
    date(2024, 3, 8): "Международный женский день",
    date(2024, 5, 1): "Праздник Весны и Труда",
    date(2024, 5, 9): "День Победы",
    date(2024, 6, 12): "День России",
}

weekdays_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
start_date = date(2024, 1, 1)
end_date = date(2024, 5, 27)

current_date = start_date

while current_date <= end_date:
    holiday_name = HOLIDAYS.get(current_date)
    cur.execute(
        """INSERT INTO dim_date (real_date, year, month, day, weekday, holiday)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            current_date,
            current_date.year,
            current_date.month,
            current_date.day,
            weekdays_ru[current_date.weekday()],
            holiday_name
        )
    )
    current_date += timedelta(days=1)

#заполнение 
cafes = [
    ("Центральная", "Центр", date(2020, 3, 1)),
    ("Садовая", "Центр", date(2021, 6, 15)),
    ("Бутовская мечта", "Новая Москва", date(2023, 4, 16)),
    ("Коммунарское солнце", "Новая Москва", date(2024, 5, 12))
]

for cafe in cafes:
    cur.execute("INSERT INTO dim_cafe (name, district, open_date) VALUES (%s, %s, %s)", cafe)

#заполнение dim_product
products_data = [
    (1, "Американо", "Напитки", 150.00),
    (2, "Капучино", "Напитки", 200.00),
    (3, "Латте", "Напитки", 220.00),
    (4, "Эспрессо", "Напитки", 120.00),
    (5, "Раф", "Напитки", 250.00),
    (6, "Какао", "Напитки", 180.00),
    (7, "Круассан", "Выпечка", 130.00),
    (8, "Чизкейк", "Десерты", 280.00),
    (9, "Маффин", "Выпечка", 160.00),
    (10, "Сэндвич", "Еда", 300.00),
    (11, "Салат", "Еда", 250.00),
    (12, "Печенье", "Выпечка", 90.00),
    (13, "Чай черный", "Напитки", 100.00),
    (14, "Чай зеленый", "Напитки", 100.00),
    (15, "Морс", "Напитки", 140.00),
]
# Словарь: product_key -> (product_id, valid_from, valid_to)
product_info = {}

for pid, name, category, price in products_data:
    cur.execute(
        """INSERT INTO dim_product (product_id, name, category, base_price, valid_from, valid_to, is_current)
           VALUES (%s, %s, %s, %s, %s, NULL, TRUE) RETURNING product_key""",
        (pid, name, category, price, start_date)
    )
    pk = cur.fetchone()[0]
    product_info[pk] = {"product_id": pid, "valid_from": start_date, "valid_to": None}

price_changes = [
    (2, 220.00, date(2024, 4, 1)),   # Капучино подорожал до 220
    (7, 150.00, date(2024, 3, 15)),   # Круассан подорожал до 150
]

for pid, new_price, change_date in price_changes:
    # Закрываем старую версию
    cur.execute(
        """UPDATE dim_product
           SET valid_to = %s, is_current = FALSE
           WHERE product_id = %s AND is_current = TRUE""",
        (change_date - timedelta(days=1), pid)
    )

    # Вставляем новую версию
    cur.execute(
        """SELECT name, category FROM dim_product
           WHERE product_id = %s AND is_current = FALSE
           ORDER BY product_key DESC LIMIT 1""",
        (pid,)
    )
    name, category = cur.fetchone()

    cur.execute(
        """INSERT INTO dim_product (product_id, name, category, base_price, valid_from, valid_to, is_current)
           VALUES (%s, %s, %s, %s, %s, NULL, TRUE) RETURNING product_key""",
        (pid, name, category, new_price, change_date)
    )
    pk = cur.fetchone()[0]
    product_info[pk] = {"product_id": pid, "valid_from": change_date, "valid_to": None}


#обновляем product_info

product_info = {}
cur.execute("SELECT product_key, product_id, valid_from, valid_to FROM dim_product")
for pk, pid, vf, vt in cur.fetchall():
    product_info[pk] = {"product_id": pid, "valid_from": vf, "valid_to": vt}

def get_product_key(pid, order_date):
    """Возвращает product_key для product_id, действующий на order_date"""
    for pk, info in product_info.items():
        if info["product_id"] != pid:
            continue
        vf = info["valid_from"]
        vt = info["valid_to"]
        if vf <= order_date and (vt is None or vt >= order_date):
            return pk
    return None

cafes_profiles = [
    ("Центральная", "Центр", date(2020, 3, 1), 120, True, True, False),
    ("Садовая", "Центр", date(2021, 6, 15), 100, True, True, True),
    ("Бутовская мечта", "Новая Москва", date(2023, 4, 16), 70, False, False, True),
    ("Коммунарское солнце", "Новая Москва", date(2024, 5, 12), 50, False, True, True),
]

# Получаем cafe_id из БД
cafe_profiles = []
for name, district, open_date, traffic, morning, lunch, evening in cafes_profiles:
    cur.execute("SELECT cafe_id FROM dim_cafe WHERE name = %s", (name,))
    row = cur.fetchone()
    if row is None:
        print(f"  ⚠️ Кофейня '{name}' не найдена в dim_cafe, пропускаем")
        continue
    cafe_profiles.append({
        "cafe_id": row[0],
        "base_traffic": traffic,
        "morning": morning,
        "lunch": lunch,
        "evening": evening,
        "district": district
    })

# Веса популярности товаров
product_weights = []
for pid, name, category, price in products_data:
    if pid in [11, 12, 14]:  # Салат, Печенье, Чай зеленый — мертвый груз
        product_weights.append(0.5)
    elif pid in [8, 10]:  # Чизкейк, Сэндвич — средние
        product_weights.append(1.5)
    else:
        product_weights.append(5.0)

# Веса глубины чека
item_count_weights = [0.05, 0.20, 0.35, 0.25, 0.10, 0.04, 0.01]

# Веса скидок
discount_options = [0.00, 5.00, 10.00, 15.00, 20.00]
discount_weights = [60, 15, 12, 8, 5]

OPENING_HOURS = list(range(7, 23))

# Получаем date_id из БД
cur.execute("SELECT date_id, real_date, weekday FROM dim_date")
date_rows = cur.fetchall()
date_info = {row[1]: {"id": row[0], "weekday": row[2]} for row in date_rows}

total_orders = 0

for current_date in sorted(date_info.keys()):
    info = date_info[current_date]
    date_id = info["id"]
    weekday = info["weekday"]
    is_holiday = current_date in HOLIDAYS
    is_weekend = weekday in ["Суббота", "Воскресенье"]

    for cafe in cafe_profiles:
        # Расчёт количества заказов
        base = cafe["base_traffic"]

        if is_weekend:
            if cafe["district"] == "Центр":
                base = int(base * 0.7)
            elif cafe["district"] == "Новая Москва":
                base = int(base * 1.1)
        else:
            if cafe["district"] == "Новая Москва":
                base = int(base * 0.8)

        if is_holiday:
            base = int(base * 0.5)

        base = int(base * random.uniform(0.8, 1.2))
        num_orders = max(5, base)

        # Веса часов
        hour_weights = []
        for h in OPENING_HOURS:
            w = 1.0
            if 7 <= h <= 10 and cafe["morning"]:
                w *= 3.0
            if 12 <= h <= 14 and cafe["lunch"]:
                w *= 3.5
            if 17 <= h <= 20 and cafe["evening"]:
                w *= 3.0
            if h in [15, 16]:
                w *= 0.4
            if h >= 21:
                w *= 0.3
            hour_weights.append(w)

        total_w = sum(hour_weights)
        hour_probs = [w / total_w for w in hour_weights]

        for _ in range(num_orders):
            order_hour = random.choices(OPENING_HOURS, weights=hour_probs, k=1)[0]
            order_minute = random.randint(0, 59)
            order_time = time(order_hour, order_minute)

            cur.execute(
                "INSERT INTO fact_orders (date_id, cafe_id, order_time) VALUES (%s, %s, %s) RETURNING order_id",
                (date_id, cafe["cafe_id"], order_time)
            )
            order_id = cur.fetchone()[0]
            total_orders += 1

            # Позиции в заказе
            num_items = random.choices(range(1, 8), weights=item_count_weights, k=1)[0]
            chosen = random.choices(products_data, weights=product_weights, k=min(num_items, len(products_data)))

            for pid, name, category, price in chosen:
                qty = random.choices([1, 2, 3], weights=[70, 20, 10], k=1)[0]
                discount = random.choices(discount_options, weights=discount_weights, k=1)[0]
                pk = get_product_key(pid, current_date)

                cur.execute(
                    """INSERT INTO fact_orders_item (order_id, product_key, quantity, discount_pct)
                       VALUES (%s, %s, %s, %s)""",
                    (order_id, pk, qty, discount)
                )

        if total_orders % 5000 == 0:
            db_connection.commit()
            print(f"  Сгенерировано {total_orders} заказов...")

db_connection.commit()

