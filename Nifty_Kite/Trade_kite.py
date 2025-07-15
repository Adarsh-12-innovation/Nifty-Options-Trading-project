import math
from enum import Enum

from kiteconnect import KiteConnect

exchange_dict = None


class Trade(Enum):
    LONG_POSITION = "long"
    SHORT_POSITION = "short"
    NONE = "none"



def get_strike_price_from_index_indicator(index, indicator):
    strike_price = 0
    if indicator == Trade.LONG_POSITION:
        strike_price = int(math.floor(index / 100)) * 100
        strike_price = strike_price - 200
    elif indicator == Trade.SHORT_POSITION:
        strike_price = int(math.ceil(index / 100)) * 100
        strike_price = strike_price + 200

    return strike_price


def buy_contract(contract_row, quantity_, real_trade, kite: KiteConnect):
    global exchange_dict
    if exchange_dict is None:
        initialize_exchange_dict(kite)
    try:
        log_str = contract_row['tradingsymbol'] + " " + "quantity:" + str(quantity_) + " " + \
                  exchange_dict.get(
                      contract_row['exchange']) + " " + kite.TRANSACTION_TYPE_BUY + " " + kite.VARIETY_REGULAR + \
                  " " + kite.PRODUCT_NRML + " " + kite.ORDER_TYPE_MARKET
        if not real_trade:
            return True, 0, log_str
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange_dict.get(contract_row['exchange']),
            tradingsymbol=contract_row['tradingsymbol'],
            transaction_type=kite.TRANSACTION_TYPE_BUY,
            quantity=quantity_,
            product=kite.PRODUCT_NRML,
            order_type=kite.ORDER_TYPE_MARKET
        )
        return True, order_id, log_str
    except Exception as e:
        print("Order placement failed: {}".format(e))
    return False, False, "Error during order"


def sell_contract(contract_row, quantity_, real_trade, kite: KiteConnect):
    global exchange_dict
    log_str = ""
    if exchange_dict is None:
        initialize_exchange_dict(kite)
    try:
        log_str = contract_row['tradingsymbol'] + " " + "quantity:" + str(quantity_) + " " + \
                  exchange_dict.get(
                      contract_row['exchange']) + " " + kite.TRANSACTION_TYPE_SELL + " " + kite.VARIETY_REGULAR + \
                  " " + kite.PRODUCT_NRML + " " + kite.ORDER_TYPE_MARKET
        if not real_trade:
            return True, 0, log_str
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange_dict.get(contract_row['exchange']),
            tradingsymbol=contract_row['tradingsymbol'],
            transaction_type=kite.TRANSACTION_TYPE_SELL,
            quantity=quantity_,
            product=kite.PRODUCT_NRML,
            order_type=kite.ORDER_TYPE_MARKET
        )
        return True, order_id, log_str
    except Exception as e:
        log_str = log_str + "-------" +e.__str__()
        print("Order placement failed: {}".format(e))
    return False, False, log_str


def initialize_exchange_dict(kite):
    global exchange_dict
    exchange_dict = {
        'NFO': kite.EXCHANGE_NFO,
        'NSE': kite.EXCHANGE_NSE,
        'BCD': kite.EXCHANGE_BCD,
        'BFO': kite.EXCHANGE_BFO,
        'BSE': kite.EXCHANGE_BSE,
        'CDS': kite.EXCHANGE_CDS,
        'MCX': kite.EXCHANGE_MCX
    }
