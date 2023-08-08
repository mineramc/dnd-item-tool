import tkinter as tk
from dotenv import dotenv_values
import os
import MySQLdb
import hashlib

config = dotenv_values(".env")
connection = MySQLdb.connect(
    host=config["HOST"],
    user=config["USERNAME"],
    passwd=config["PASSWORD"],
    db=config["DATABASE"],
    autocommit=True,
    ssl_mode="VERIFY_IDENTITY",
    ssl={
        "ca": "./cacert-2023-05-30.pem"
    }
)
c = connection.cursor()


def init():
    c.execute("""
        DROP TABLE items
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id varchar(255),
            name VARCHAR(255),
            rarity VARCHAR(255),
            item_type VARCHAR(255),
            description TEXT,
            effect TEXT,
            tags JSON,
            additional JSON,
            source VARCHAR(255),
            PRIMARY KEY (id)
        )
    """)
    window = tk.Tk()


def insert_item(name, rarity, item_type, desc, effect, tags, additional, source):
    """
    Creates and inserts an item into the sql database. Duplicate (determined based off of name and rarity) entries will
    be replaced on write
    :param name: Name of the item to be inserted
    :param rarity: Rarity of the item to be inserted
    :param item_type: Type of the item (e.g Wondrous Item, greatsword, etc.)
    :param desc: Description of the item's qualities/looks
    :param effect: Gameplay effect of the item
    :param tags:
    :param additional: Additional fields that may be added as needed in json format
    :param source:
    :return:
    """
    sql = f"""
            REPLACE INTO items (id, name, rarity, item_type, description, effect, tags, additional, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
    h = hashlib.sha256()
    h.update(bytes(name + rarity, 'utf-8'))
    vals = (h.hexdigest(), name, rarity, item_type, desc, effect, tags, additional, source)
    c.execute(sql, vals)


def get_items_by_name(name):
    sql = f"""
            SELECT * from items
            WHERE name = %s
        """
    vals = (name, )
    c.execute(sql, vals)
    return c.fetchall()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init()
    insert_item("TEST", "TEST", "TEST", "TEST", "TEST", "{\"TEST\": \"TEST\"}", "{\"TEST\": \"TEST\"}", "TEST")
    print(get_items_by_name("TEST"))
    insert_item("TEST", "TEST", "TEST2", "TEST2", "TEST2", "{\"TEST2\": \"TEST\"}", "{\"TEST\": \"TEST\"}", "TEST")
    print(get_items_by_name("TEST"))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
