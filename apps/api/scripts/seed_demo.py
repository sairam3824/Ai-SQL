from __future__ import annotations

import random
import sqlite3
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "demo"
SQLITE_PATH = DATA_DIR / "sales_demo.sqlite"
DUCKDB_PATH = DATA_DIR / "sales_demo.duckdb"

CUSTOMERS = [
    ("Acme Retail", "North"),
    ("Blue Harbor", "West"),
    ("Cedar Labs", "South"),
    ("Delta Stores", "East"),
    ("Evergreen Foods", "North"),
    ("Futura Health", "West"),
    ("Golden Cart", "East"),
    ("Helio Works", "South"),
    ("Indigo Supply", "North"),
    ("Juniper Goods", "West"),
]

PRODUCTS = [
    ("Analytics", "Insight Pro", 149.0),
    ("Analytics", "Insight Lite", 89.0),
    ("Hardware", "Beacon Sensor", 260.0),
    ("Hardware", "Fleet Hub", 320.0),
    ("Services", "Launch Pack", 600.0),
    ("Services", "Success Plan", 420.0),
    ("Commerce", "Checkout Max", 190.0),
    ("Commerce", "Cart Boost", 110.0),
]


def month_start(day: date) -> date:
    return date(day.year, day.month, 1)


def subtract_months(day: date, months: int) -> date:
    year = day.year
    month = day.month - months
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def iter_months(count: int) -> list[date]:
    today = date.today()
    current = month_start(today)
    return [subtract_months(current, offset) for offset in reversed(range(count))]


def build_rows() -> tuple[list[tuple], list[tuple], list[tuple], list[tuple], list[tuple]]:
    random.seed(17)
    customers = [
        (index + 1, name, region, subtract_months(date.today(), random.randint(6, 24)).isoformat())
        for index, (name, region) in enumerate(CUSTOMERS)
    ]
    products = [
        (index + 1, category, name, price)
        for index, (category, name, price) in enumerate(PRODUCTS)
    ]

    orders: list[tuple] = []
    order_items: list[tuple] = []
    events: list[tuple] = []
    order_id = 1
    order_item_id = 1
    event_id = 1

    for month_index, month in enumerate(iter_months(18)):
        for customer_id, _, _, _ in customers:
            event_volume = random.randint(3, 8)
            for _ in range(event_volume):
                day = month + timedelta(days=random.randint(0, 26))
                events.append(
                    (
                        event_id,
                        customer_id,
                        random.choice(["login", "report_view", "export"]),
                        datetime.combine(day, datetime.min.time()).isoformat(),
                    )
                )
                event_id += 1

            order_volume = random.randint(1, 4)
            for _ in range(order_volume):
                ordered_day = month + timedelta(days=random.randint(0, 26))
                status = random.choice(["paid", "paid", "paid", "refunded"])
                subtotal = 0.0
                line_count = random.randint(1, 3)
                chosen_products = random.sample(products, k=line_count)
                for product in chosen_products:
                    product_id = product[0]
                    quantity = random.randint(1, 5)
                    price = product[3]
                    # Create a seasonal drop for Commerce products in the latest quarter.
                    if product[1] == "Commerce" and month_index > 13:
                        price *= 0.72
                    if product[1] == "Analytics" and month_index > 10:
                        price *= 1.18
                    line_total = round(quantity * price, 2)
                    subtotal += line_total
                    order_items.append(
                        (
                            order_item_id,
                            order_id,
                            product_id,
                            quantity,
                            round(price, 2),
                            line_total,
                        )
                    )
                    order_item_id += 1
                tax = round(subtotal * 0.08, 2)
                total = round(subtotal + tax, 2)
                orders.append(
                    (
                        order_id,
                        customer_id,
                        datetime.combine(ordered_day, datetime.min.time()).isoformat(),
                        status,
                        round(subtotal, 2),
                        tax,
                        total,
                    )
                )
                order_id += 1

    return customers, products, orders, order_items, events


def reset_sqlite(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.executescript(
        """
        DROP TABLE IF EXISTS user_events;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            region TEXT NOT NULL,
            signup_date TEXT NOT NULL
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            unit_price REAL NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            ordered_at TEXT NOT NULL,
            status TEXT NOT NULL,
            subtotal REAL NOT NULL,
            tax REAL NOT NULL,
            total_amount REAL NOT NULL
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            line_total REAL NOT NULL
        );

        CREATE TABLE user_events (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL REFERENCES customers(id),
            event_name TEXT NOT NULL,
            occurred_at TEXT NOT NULL
        );

        CREATE INDEX idx_orders_ordered_at ON orders (ordered_at);
        CREATE INDEX idx_orders_customer_id ON orders (customer_id);
        CREATE INDEX idx_order_items_product_id ON order_items (product_id);
        CREATE INDEX idx_user_events_occurred_at ON user_events (occurred_at);
        """
    )
    connection.commit()


def reset_duckdb(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute(
        """
        DROP TABLE IF EXISTS user_events;
        DROP TABLE IF EXISTS order_items;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS products;
        DROP TABLE IF EXISTS customers;

        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            region VARCHAR NOT NULL,
            signup_date DATE NOT NULL
        );

        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            category VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            unit_price DOUBLE NOT NULL
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            ordered_at TIMESTAMP NOT NULL,
            status VARCHAR NOT NULL,
            subtotal DOUBLE NOT NULL,
            tax DOUBLE NOT NULL,
            total_amount DOUBLE NOT NULL
        );

        CREATE TABLE order_items (
            id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DOUBLE NOT NULL,
            line_total DOUBLE NOT NULL
        );

        CREATE TABLE user_events (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            event_name VARCHAR NOT NULL,
            occurred_at TIMESTAMP NOT NULL
        );

        CREATE INDEX idx_orders_ordered_at ON orders (ordered_at);
        CREATE INDEX idx_orders_customer_id ON orders (customer_id);
        CREATE INDEX idx_order_items_product_id ON order_items (product_id);
        CREATE INDEX idx_user_events_occurred_at ON user_events (occurred_at);
        """
    )


def bulk_insert(
    sqlite_conn: sqlite3.Connection,
    duckdb_conn: duckdb.DuckDBPyConnection,
    table: str,
    rows: Iterable[tuple],
) -> None:
    rows = list(rows)
    placeholder = ", ".join(["?"] * len(rows[0]))
    sqlite_conn.executemany(f"INSERT INTO {table} VALUES ({placeholder})", rows)
    duckdb_conn.executemany(f"INSERT INTO {table} VALUES ({placeholder})", rows)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    customers, products, orders, order_items, events = build_rows()

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    duckdb_conn = duckdb.connect(str(DUCKDB_PATH))

    try:
        reset_sqlite(sqlite_conn)
        reset_duckdb(duckdb_conn)
        bulk_insert(sqlite_conn, duckdb_conn, "customers", customers)
        bulk_insert(sqlite_conn, duckdb_conn, "products", products)
        bulk_insert(sqlite_conn, duckdb_conn, "orders", orders)
        bulk_insert(sqlite_conn, duckdb_conn, "order_items", order_items)
        bulk_insert(sqlite_conn, duckdb_conn, "user_events", events)
        sqlite_conn.commit()
        duckdb_conn.commit()
    finally:
        sqlite_conn.close()
        duckdb_conn.close()

    print(f"Created demo SQLite database at {SQLITE_PATH}")
    print(f"Created demo DuckDB database at {DUCKDB_PATH}")


if __name__ == "__main__":
    main()
