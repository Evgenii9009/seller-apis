import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page, campaign_id, access_token):
    """Get products list from Yandex Market website

    Args:
        page (int): number of page which should be received
        campaign_id (str): Market ID for Yandex Market
        access_token (str): Seller token for Yandex Market

    Results:
       (dict): data about product from Yandex Market

    Raises: 
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> page = 40
        >>> market_token = env.str("MARKET_TOKEN")
        >>> campaign_fbs_id = env.str("FBS_ID")
        >>> get_product_list((page, campaign_fbs_id, access_token)
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks, campaign_id, access_token):
    """Uploads stocks to the Yandex Market website

    Args:
        stocks (list): List of products stocks
        campaign_id (str): Market ID for Yandex Market
        access_token (str): Seller token for Yandex Market
    
    Returns:
        (dict): Dict with response from Yandex Market

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> stocks = [{'sku': '73397', 'warehouseId': 'WAREHOUSE_ID', 'items': [{'count': 100, 'type': 'FIT', 'updatedAt': '2025-02-06T08:53:21Z'}]}]
        >>> market_token = env.str("MARKET_TOKEN")
        >>> campaign_fbs_id = env.str("FBS_ID")
        >>> update_stocks((stocks, campaign_fbs_id, market_token)
        response.json()
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices, campaign_id, access_token):
    """
    Updates prices for products on Yandex Market website

    Args:
        prices (list): List of prices on products
        campaign_id (str): Market ID for Yandex Market
        access_token (str): Seller token for Yandex Market

    Returns:
        (dict): Dict with response from Yandex Market

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> prices = [{'id': '73397', 'price': {'value': 22990, 'currencyId': 'RUR'}}]
        >>> market_token = env.str("MARKET_TOKEN")
        >>> campaign_fbs_id = env.str("FBS_ID")
        >>> update_prices((prices, campaign_fbs_id, market_token)
        response.json()
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id, market_token):
    """Get products IDs from Yandex Market website
    
    Args:
        campaign_id (str): Market ID for Yandex Market
        market_token (str): Seller token for Yandex Market

    Returns:
        offer_ids (list): list of goods IDs from Yandex Market

    Raises: 
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website
    
    Example:
        >>> market_token = env.str("MARKET_TOKEN")
        >>> campaign_fbs_id = env.str("FBS_ID")
        >>> get_offer_ids(campaign_id, market_token)
        ['73397', '73398', '73399']
    """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants, offer_ids, warehouse_id):
    """
    Calculate amounts of stocks of watches in warehouse by data from casio and Yandex Market

    Args:
        watch_remnants (dict): Watches data from casio website
        offer_ids (list): List with product IDs from Yandex Market
        warehouse_id (str): Warehouse ID
        
    Returns:
        stocks (list): List of dicts, every dict contains Yandex Market ID and amount of watches in warehouse for this id

    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> offer_ids = [73397, 73398, 73399]
        >>> warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID") 
        >>> create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        [{'sku': '73397', 'warehouseId': 'WAREHOUSE_ID', 'items': [{'count': 100, 'type': 'FIT', 'updatedAt': '2025-02-06T08:53:21Z'}]}, 
        {'sku': '73398', 'warehouseId': 'WAREHOUSE_ID', 'items': [{'count': 0, 'type': 'FIT', 'updatedAt': '2025-02-06T08:53:21Z'}]},
        {'sku': '73399', 'warehouseId': 'WAREHOUSE_ID', 'items': [{'count': 0, 'type': 'FIT', 'updatedAt': '2025-02-06T08:53:21Z'}]}]       
    """
    # Уберем то, что не загружено в market
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    # Добавим недостающее из загруженного:
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants, offer_ids):
    """
    Creates prices with conversion from watches data if watch number is in Yandex Market ids

    Args:
        watch_remnants (dict): Watches data from casio website
        offer_ids (list): List with product IDs from Yandex Market

    Returns:
        prices (list): List of dicts, every dict contains data about watch price for Yandex Market

    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> offer_ids = [73397, 73398, 73399]
        >>> create_prices(watch_remnants, offer_ids)
    [{'id': '73397', 'price': {'value': 22990, 'currencyId': 'RUR'}}]
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants, campaign_id, market_token):
    """
    Gets product IDs from Yandex Market, gets prices from watch_remnants, update prices on Yandex Market 
    Args:
        watch_remnants (dict): Watches data from casio website
        campaign_id (str): Market ID for Yandex Market
        market_token (str): Seller token for Yandex Market

    Returns:
        prices (list): List of dicts, every dict contains data about watch price for Yandex Market

    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website

    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> market_token = env.str("MARKET_TOKEN")
        >>> campaign_fbs_id = env.str("FBS_ID")
        >>> upload_prices(watch_remnants, campaign_fbs_id, market_token)
        [{'auto_action_enabled': 'UNKNOWN', 'currency_code': 'RUB', 'offer_id': '73397', 'old_price': '0', 'price': '22990'}]
    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants, campaign_id, market_token, warehouse_id):
    """
    Gets product IDs from Yandex Market, gets stocks from watch_remnants, update stocks on Yandex Market
    Args:
        watch_remnants (dict): Watches data from casio website
        campaign_id (str): Market ID for Yandex Market
        market_token (str): Seller token for Yandex Market
        warehouse_id (str): Warehouse ID
    
    Returns:
        not_empty (list): List of stocks, except for those that =0
        stocks (list): List of dicts, every dict contains Yandex Market id and amount of watches for this id in warehouse
    
    Raises:
        HTTPError: If response with code 4xx or 5xx
        ConnectionError: If problems with connection to the website
    
    Example:
        >>> watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
        >>> market_token = env.str("MARKET_TOKEN")
        >>> campaign_fbs_id = env.str("FBS_ID")
        >>> upload_prices(watch_remnants, campaign_fbs_id, market_token, warehouse_id)
        [{'offer_id': '73397', 'stock': 100}], [{'offer_id': '73398', 'stock': 0}, {'offer_id': '73399', 'stock': 0}]
    """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
    """
    Gets product IDs from Yandex Market, gets stocks from casio website, update prices and stocks on Yandex Market

    Raises:
        "Превышено время ожидания...": If ReadTimeout
        "Ошибка соединения": If ConnectionError
        "ERROR_2": If other errors
    """
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        # FBS
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        # Обновить остатки FBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        # Поменять цены FBS
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        # DBS
        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        # Обновить остатки DBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        # Поменять цены DBS
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
