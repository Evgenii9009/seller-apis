import re
import datetime

def create_prices(watch_remnants, offer_ids):
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    "currencyId": "RUR",
                }}
            prices.append(price)
    return prices

def create_stocks(watch_remnants, offer_ids, warehouse_id):
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



def price_conversion(price: str) -> str:
    return re.sub("[^0-9]", "", price.split(".")[0])


watch_remnants = [{'Код': 73397, 'Наименование товара': 'BA-110FH-2A',
                            'Изображение': 'http://www.timeworld.ru/products/itshow.php?id=73397',
                            'Цена': "22'990.00 руб.", 'Количество': '>10'}]
offer_ids = ['73397', '73398', '73399']
warehouse_id = 'WAREHOUSE_ID'
stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
print(stocks)