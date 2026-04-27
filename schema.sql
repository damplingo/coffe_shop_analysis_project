-- schema.sql
-- Создание таблиц для сети кофеен Urban Coffee

-- Измерения
CREATE TABLE dim_date (
    date_id     SERIAL PRIMARY KEY,
    real_date   DATE NOT NULL,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    day         INTEGER NOT NULL,
    weekday     VARCHAR(50) NOT NULL,
    holiday     VARCHAR(50) DEFAULT ''
);

CREATE TABLE dim_cafe (
    cafe_id     SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    district    VARCHAR(50) NOT NULL,
    open_date   DATE NOT NULL
);

CREATE TABLE dim_product (
    product_key  SERIAL PRIMARY KEY,
    product_id   INTEGER NOT NULL,
    name         VARCHAR(100) NOT NULL,
    category     VARCHAR(50) NOT NULL,
    base_price   DECIMAL(10,2) NOT NULL,
    valid_from   DATE NOT NULL,
    valid_to     DATE,
    is_current   BOOLEAN DEFAULT TRUE
);

-- Факты
CREATE TABLE fact_orders (
    order_id    SERIAL PRIMARY KEY,
    date_id     INTEGER NOT NULL REFERENCES dim_date(date_id),
    cafe_id     INTEGER NOT NULL REFERENCES dim_cafe(cafe_id),
    order_time  TIME NOT NULL
);

CREATE TABLE fact_orders_item (
    order_item_id  SERIAL PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES fact_orders(order_id),
    product_key    INTEGER NOT NULL REFERENCES dim_product(product_key),
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    discount_pct   DECIMAL(10,2) DEFAULT 0.00
);