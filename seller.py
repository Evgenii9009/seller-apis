import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id, client_id, seller_token):
    """Get products list from OZON website

    Args:
        last_id (str): ID of previous product which was received
        client_id (str): Client ID for OZON
        seller_token (str): Seller token fro OZON

    Results:
       (dict): Data about product from OZON

    Raises: 
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> last_id = ""
        >>> client_id = env.str("CLIENT_ID")
        >>> seller_token = env.str("SELLER_TOKEN")
        >>> get_product_list(last_id, client_id, seller_token)
    """
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id, seller_token):
    """Get products IDs from OZON website
    
    Args:
        client_id (str): Client ID for OZON
        seller_token (str): Seller token fro OZON

    Returns:
        offer_ids (list): list of products IDs from OZON

    Raises: 
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website
    
    Example:
        >>> seller_token = env.str("SELLER_TOKEN")
        >>> client_id = env.str("CLIENT_ID")
        >>> get_offer_ids(client_id, seller_token)
        ['73397', '73398', '73399']
    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id, seller_token):
    """
    Updates prices for products on OZON website

    Args:
        prices (list): List of prices on watches
        client_id (str): Client ID for OZON
        seller_token (str): Seller token fro OZON

    Returns:
        (dict): Dict with response from OZON

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> prices = [{'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB', 'offer_id': '73397', 'old_price': '0', 'price': '22990'}]
        >>> seller_token = env.str("SELLER_TOKEN")
        >>> client_id = env.str("CLIENT_ID")
        >>> update_price(prices, client_id, seller_token)
        response.json()
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id, seller_token):
    """Uploads stocks to the OZON website

    Args:
        stocks (list): List of watches stocks
        client_id (str): Client ID for OZON
        seller_token (str): Seller token fro OZON
    
    Returns:
        (dict): Dict with response from OZON

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> stocks = [{'offer_id': '73397', 'stock': 100}, {'offer_id': '73398', 'stock': 0}, {'offer_id': '73399', 'stock': 0}]
        >>> seller_token = env.str("SELLER_TOKEN")
        >>> client_id = env.str("CLIENT_ID")
        >>> update_stocks(stocks, client_id, seller_token)
        response.json()
    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock():
    """
    Download xls-file with watches and converts it to list of dicts

    Returns:
        watch_remnants (list):  List of dicts, every dict contains data about one watch

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> download_stocks()
        [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
        'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
        'Цена': "22'990.00 руб.", 'Количество': '>10'}]
    """
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")
    return watch_remnants


def create_stocks(watch_remnants, offer_ids):
    """
    Calculate amounts of stocks of watches by data from casio and OZON

    Args:
        watch_remnants (dict): Watches data from casio website
        offer_ids (list): List with ids from OZON
    
    Returns:
        stocks (list): List of dicts, every dict contains OZON id and amount of watches for this id

    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> offer_ids = [73397, 73398, 73399]
        >>> create_stocks(watch_remnants, offer_ids)
        [{'offer_id': '73397', 'stock': 100}, {'offer_id': '73398', 'stock': 0}, {'offer_id': '73399', 'stock': 0}]        
    """
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants, offer_ids):
    """
    Creates prices with conversion from watches data if watch number is in OZON ids

    Args:
        watch_remnants (dict): Watches data from casio website
        offer_ids (list): List with ids from OZON

    Returns:
        prices (list): List of dicts, every dict contains data about watch price for OZON

    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> offer_ids = [73397, 73398, 73399]
        >>> create_prices(watch_remnants, offer_ids)
    [{'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB', 'offer_id': '73397', 'old_price': '0', 'price': '22990'}]
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """
    Converts the price by removing the fractional part and the currency

    Args:
        price (str): Price from casio website

    Returns:
        str: String with а replacement of [^0-9] fragment to "" in converted price

    Raises:
        TypeError: If price is not a string

    Example:
        >>> price = '5'990.00 руб.'
        >>> price_conversion(price)
        '5990'
   """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """
    Divide the list into parts of n elements, returns one part per run

    Args:
        lst (list): The list that needs to be divided
        n (int): Number of elements in one part

    Returns:
        lst: One part of the initial list, contains n elements

    Example:
        >>> lst = [1, 2, 3, 4]
        >>> n = 1
        >>> divide(lst, n)
        1
        >>> divide(lst, n)
        2
    """
    for i in range(0, len(lst), n):
        yield lst[i: i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    """
    Gets the IDs from OZON, gets prices from watch_remnants, update prices on OZON 
    Args:
        watch_remnants (dict): Watches data from casio website
        client_id (str): Client ID for OZON
        seller_token (str): Seller token for OZON

    Returns:
        prices (list): List of dicts, every dict contains data about watch price for OZON

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> seller_token = env.str("SELLER_TOKEN")
        >>> client_id = env.str("CLIENT_ID")
        >>> upload_prices(watch_remnants, client_id, seller_token)
        [{'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB', 'offer_id': '73397', 'old_price': '0', 'price': '22990'}]
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """
    Gets the IDs from OZON, gets stocks from watch_remnants, update stocks on OZON
    Args:
        watch_remnants (dict): Watches data from casio website
        client_id (str): Client ID for OZON
        seller_token (str): Seller token fro OZON
    
    Returns:
        not_empty (list): List of stocks, except for those that =0
        stocks (list): List of dicts, every dict contains OZON id and amount of watches for this id
    
    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website
    
    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> seller_token = env.str("SELLER_TOKEN")
        >>> client_id = env.str("CLIENT_ID")
        >>> upload_stocks(watch_remnants, client_id, seller_token)
        [{'offer_id': '73397', 'stock': 100}], [{'offer_id': '73398', 'stock': 0}, {'offer_id': '73399', 'stock': 0}]
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    """
    Gets IDs from OZON, gets stocks from casio website, update prices and stocks on OZON

    Raises:
        "Превышено время ожидания...": If ReadTimeout
        "Ошибка соединения": If ConnectionError
        "ERROR_2": If other errors
    """
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        # Обновить остатки
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        # Поменять цены
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
