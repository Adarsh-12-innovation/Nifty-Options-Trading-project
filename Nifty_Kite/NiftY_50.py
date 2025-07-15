from datetime import datetime
from typing import Tuple

from kiteconnect import KiteConnect
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

from fileUtls import is_file_created_or_modified_today, read_from_pickle_file, write_to_pickle_file
from strategy_globals import start_time, end_time
from global_strings import nifty_nse_instruments_file, nifty_wikipidea_list, nifty_kite_instruments, instruments_csv


def get_nifty_symbols() -> list:
    if is_file_created_or_modified_today(nifty_wikipidea_list):
        wikipidea_list = read_from_pickle_file(nifty_wikipidea_list)
        return wikipidea_list
    # r = requests.get("https://en.wikipedia.org/wiki/NIFTY_50")
    # soup = bs(r.content, "html.parser")
    # table = soup.find("table", attrs={"id": "constituents"})
    # columns = table.find("tr").find_all("th")
    # column_names = [str(c.string).strip() for c in columns]
    #
    # table_rows = table.find("tbody").find_all("tr")
    # l = []
    # for tr in table_rows:
    #     td = tr.find_all('td')
    #     row = [str(tr.get_text()).strip() for tr in td]
    #     l.append(row)
    #
    # df = pd.DataFrame(l, columns=column_names)
    # df = df.dropna(axis=0)
    # wikipidea_list = df['Symbol'].tolist()
    wikipidea_list = [
    'ADANIENT', 'ADANIPORTS', 'APOLLOHOSP', 'ASIANPAINT', 'AXISBANK', 'BAJAJ-AUTO',
    'BAJFINANCE', 'BAJAJFINSV', 'BPCL', 'BHARTIARTL', 'BRITANNIA', 'CIPLA', 'COALINDIA',
    'DIVISLAB', 'DRREDDY', 'EICHERMOT', 'GRASIM', 'HCLTECH', 'HDFCBANK', 'HDFCLIFE',
    'HEROMOTOCO', 'HINDALCO', 'HINDUNILVR', 'ICICIBANK', 'ITC', 'INDUSINDBK', 'INFY',
    'JSWSTEEL', 'KOTAKBANK', 'LTIM', 'LT', 'M&M', 'MARUTI', 'NTPC', 'NESTLEIND', 'ONGC',
    'POWERGRID', 'RELIANCE', 'SBILIFE', 'SBIN', 'SUNPHARMA', 'TCS', 'TATACONSUM',
    'TATAMOTORS', 'TATASTEEL', 'TECHM', 'TITAN', 'UPL', 'ULTRACEMCO', 'WIPRO'
]
    write_to_pickle_file(nifty_wikipidea_list, wikipidea_list)
    return wikipidea_list


def get_nifty50_tokens(kite: KiteConnect) -> Tuple[list, list, int]:
    ##read symbols of Nifty 50 companies
    symbol_list = get_nifty_symbols()

    if is_file_created_or_modified_today(nifty_kite_instruments):
        instrument_tokens = read_from_pickle_file(nifty_kite_instruments)
        Nifty50_token = instrument_tokens.pop()
        return instrument_tokens, symbol_list, Nifty50_token

    ##get instrument from KITE NSE if it is not current
    detailed_instruments_df = pd.DataFrame
    if is_file_created_or_modified_today(nifty_nse_instruments_file):
        detailed_instruments_df = pd.read_pickle(nifty_nse_instruments_file)
    else:
        detailed_instruments_df = pd.DataFrame(kite.instruments(exchange="NSE"))
        detailed_instruments_df.to_pickle(nifty_nse_instruments_file)
        detailed_instruments_df.to_csv(instruments_csv)

    ##get symbol_list and token list from nifty
    symbol_list_nifty_all = detailed_instruments_df["tradingsymbol"].tolist()
    instrument_list_nifty_all = detailed_instruments_df["instrument_token"].tolist()

    ##create lists for initializing dataframes and dictionary
    instrument_tokens = []

    ##save instruments for Nifty 50 companies
    for symbol in symbol_list:
        ind = symbol_list_nifty_all.index(symbol)
        instrument_tokens.append(int(instrument_list_nifty_all[ind]))

    Nifty50_token = instrument_list_nifty_all[symbol_list_nifty_all.index("NIFTY 50")]
    instrument_tokens.append(int(Nifty50_token))

    write_to_pickle_file(nifty_kite_instruments, instrument_tokens)

    del instrument_tokens[-1]

    return instrument_tokens, symbol_list, Nifty50_token


def get_NSE_holidays():
    r = requests.get("https://groww.in/p/nse-holidays")
    soup = bs(r.content, "html.parser")
    table = soup.find("table")
    columns = table.find("tbody").find("tr").find_all("p")
    column_names = [str(c.string).strip() for c in columns]
    table_rows = table.find("tbody").find_all("tr")[1:]
    l = []
    for tr in table_rows:
        td = tr.find_all('td')
        row = [str(tr.get_text()).strip() for tr in td]
        l.append(row)
    df = pd.DataFrame(l, columns=column_names)
    df = df.dropna(axis=0)
    date_list = df['Date'].tolist()
    formatted_dates = []  # Create a list to store the formatted dates
    for date_holiday in date_list:
        formatted_date = datetime.strptime(date_holiday, "%B %d, %Y")
        formatted_dates.append(formatted_date.date())

    return formatted_dates


def get_market_timings():
    today = (datetime.today()).date()
    #to be done later - check if it is a special date where market starts or ends at a different time
    if today.weekday() == 5:
        print("Today is Saturday, NSE is closed")
        return False, "Today is Saturday, NSE is closed"
    elif today.weekday() == 6:
        print("Today is Sunday, NSE is closed")
        return False, "Today is Sunday, NSE is closed"
    elif today in get_NSE_holidays():
        print("Today is NSE Holiday")
        return False, "Today is NSE Holiday, NSE is closed"
    else:
        return start_time, end_time

