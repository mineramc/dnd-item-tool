import json
import tkinter as tk
from dotenv import dotenv_values
import os
import MySQLdb
import hashlib
import xml.etree.ElementTree as ET

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
            tags JSON,
            additional JSON,
            source VARCHAR(255),
            PRIMARY KEY (id)
        )
    """)
    window = tk.Tk()


def import_from_json(filename):
    with open(filename) as fileobj:
        data = json.load(fileobj)
        # Import all items from the json
        insert_list = []
        for item in data['item']:
            try:
                desc_string = '\n'.join(item["entries"])
                h = hashlib.sha256()
                h.update(bytes(item["name"] + item["rarity"], 'utf-8'))
                item_obj = (h.hexdigest(), item["name"], item["rarity"], "Wondrous Item" if "wondrous" in data else "",
                            desc_string, "{}", "{}", item["source"])
                insert_list.append(item_obj)
            except Exception as e:
                print("Error in processing item: ", item["name"], type(e).__name__, e)

        # TODO: Import all itemgroups from the json
        sql = f"""
                    REPLACE INTO items (id, name, rarity, item_type, description, tags, additional, source)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
        values = insert_list
        c.executemany(sql, values)


def import_from_xml(filename, source):
    # Read xml file from disk and load into xml object
    xml_tree = ET.parse(filename)
    root = xml_tree.getroot()  # Root should be <elements> tag
    items_to_insert = []
    if root.tag != "elements":
        print("ERROR: root tag is not elements")
        return
    for item in root:
        if item.tag != "element":
            continue
        try:
            attrib = item.attrib
            print(attrib)
            name = attrib["name"]
            desc = item.find('description').find('p').text

            try:
                setters = item.find('setters')
                for setter in setters:
                    if setter.attrib["name"] == "rarity":
                        rarity = setter.text
                    elif setter.attrib["name"] == "category":
                        item_type = setter.text
            except AttributeError as e:
                print(f"No rarity found for item {name}, setting rarity to empty")
                rarity = ""
                item_type = ""

            h = hashlib.sha256()
            h.update(bytes(name + rarity, 'utf-8'))
            item_obj = (h.hexdigest(), name, rarity, item_type,
                        desc, "{}", "{}", source)
            items_to_insert.append(item_obj)
        except Exception as e:
            print("Error in processing item from xml: ", item.attrib, type(e).__name__, e)
    print(items_to_insert)
    sql = f"""
                        REPLACE INTO items (id, name, rarity, item_type, description, tags, additional, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
    values = items_to_insert
    c.executemany(sql, values)


def insert_item(name, rarity, item_type, desc, tags, additional, source):
    """
    Creates and inserts an item into the sql database. Duplicate (determined based off of name and rarity) entries will
    be replaced on write
    :param name: Name of the item to be inserted
    :param rarity: Rarity of the item to be inserted
    :param item_type: Type of the item (e.g Wondrous Item, greatsword, etc.)
    :param desc: Description of the item's qualities/abilities
    :param tags: Quick lookup tags for the item
    :param additional: Additional fields that may be added as needed in json format
    :param source: Sourcebook for the item
    :return:
    """
    sql = f"""
            REPLACE INTO items (id, name, rarity, item_type, description, tags, additional, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
    h = hashlib.sha256()
    h.update(bytes(name + rarity, 'utf-8'))
    vals = (h.hexdigest(), name, rarity, item_type, desc, tags, additional, source)
    c.execute(sql, vals)


def get_items_by_name(name):
    """
    Gets all items that contain the given name as a substring of their name
    :param name: substring to search for
    :return:
    """
    sql = f"""
            SELECT * from items
            WHERE LOWER(name) LIKE %s
        """
    vals = (name + '%',)
    c.execute(sql, vals)
    return c.fetchall()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    init()
    import_from_xml("xml_files/dmg-items-armor.xml", "DMG")
    print(get_items_by_name("Armor"))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
