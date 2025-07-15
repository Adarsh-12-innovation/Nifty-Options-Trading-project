import os
import platform
from datetime import datetime, time

today = datetime.now()
formatted_date = today.strftime("%d_%m_%Y")
formatted_date_hm = today.strftime("%d_%m_%Y_%H_%M")

# base path for every file
if platform.system() != 'Darwin':  # 'Darwin' is macOS
    base_path = "C:\\Users\\Administrator\\Downloads\\Nifty-project\\Nifty_Kite"
else:
    base_path = "/Users/mayamasi/Downloads/Nifty_Kite"

# previous day candle data
address_of_historical_candle_csv = os.path.join(base_path, "historical_candle", "Nifty_previous_candles.csv")
time_format = "%Y-%m-%dT%H:%M:%S"  ##time format in historical candle data
time_format2 = '%Y-%m-%d %H:%M:%S'
time_formats = [time_format, time_format2]
# time_format = "%d-%m-%Y %H:%M" ##time format in historical candle data
# for saving and accessing keys
kite_wd = base_path

# Top 50 nifty companies
nifty_wikipidea_list = os.path.join(base_path, "50_companies", "nifty50_wiki.pkl")

# nifty 50 instruments
nifty_kite_instruments = os.path.join(base_path, "50_companies", "nifty50_kite_instruments.pkl")
nifty_companies_loc = os.path.join(base_path, "50_companies", "ind_nifty50list.csv")

# Instruments from Kite:NSE
nifty_nse_instruments_file = os.path.join(base_path, "instruments", "Nifty_all_instruments.pkl")
instruments_csv = os.path.join(base_path, "instruments", "nifty_instruments.csv")

# Nifty NFO Instruments
nifty_nfo_instruments_file = os.path.join(base_path, "instruments", "NFO_all_instruments.pkl")
options_csv = os.path.join(base_path, "instruments", "nfo_instruments.csv")
nfo_call_contracts = os.path.join(base_path, "instruments", "all_call_contracts.pkl")
full_call_csv = os.path.join(base_path, "instruments", "nfo_call_all.csv")
nfo_put_contracts = os.path.join(base_path, "instruments", "all_put_contracts.pkl")
full_put_csv = os.path.join(base_path, "instruments", "nfo_put_all.csv")

nfo_call_min_expiry = os.path.join(base_path, "instruments", "call_contracts.pkl")
call_csv = os.path.join(base_path, "instruments", "nfo_call.csv")
nfo_put_min_expiry = os.path.join(base_path, "instruments", "put_contracts.pkl")
put_csv = os.path.join(base_path, "instruments", "nfo_put.csv")

put_dictionary = os.path.join(base_path, "instruments", "put_dictionary.pkl")
call_dictionary = os.path.join(base_path, "instruments", "call_dictionary.pkl")

# output logs
candle_today_file = os.path.join(base_path, "day_logs", "candle_log_" + formatted_date_hm + ".csv")
trade_today_file = os.path.join(base_path, "day_logs", "trade_log_" + formatted_date_hm + ".csv")

# trade register
trade_log_file = os.path.join(base_path, "logs", "trade_log.csv")
running_trade_file = os.path.join(base_path, "logs", "running_trade" + ".pkl")

#buy sell log
buy_sell_log_file = os.path.join(base_path, "logs", "buy_sell_log.csv")

# kite credentials
kite_creds_file = os.path.join(base_path, "key", "Amam_cred.txt")

# chrome driver
config_file = os.path.join(base_path, "key", "config.ini")
encryption_key = os.path.join(base_path, "key", "encryption_key.key")
## Column Names for saving and accessing dataframes
time_s = "time"
open_s = "open"
close_s = "close"
volume_s = "Volume"
rsi_s = "RSI"
close_ma_s = "Close MA"
volume_ma_s = "Volume MA"
gain_s = "gain"
loss_s = "loss"
avg_gain_s = "avg gain"
avg_loss_s = "avg loss"
rsi_ma_s = "rsi ma"
high_s = "high"
low_s = "low"

candle_log_format = [time_s, open_s, high_s, low_s, close_s, volume_s, volume_ma_s, rsi_s]

trade = "trade_type"
gain = "profit"
cumulative_gain = "cumulative_profit"
indicator = "indicator"
tgt = "target"
sl = "stoploss"
index_s = "ltp"

trade_log_format = [time_s, trade, indicator, index_s, tgt, sl, gain, cumulative_gain]

# Google Sheet API parameters
CLIENT_SECRET_FILE = os.path.join(base_path, "google_sheets",
                                  "client_secret_424961427997-9260qmrn8o7dht1bb8s6did958jcac1r.apps.googleusercontent.com.json")
service_account_file = os.path.join(base_path, "google_sheets", "artful-wind-402414-edfc43b570ab.json")
API_SERVICE_NAME = 'sheets'
API_VERSION = 'v4'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
token_file = os.path.join(base_path, "google_sheets", "token.pickle")
sheet_details_trade_log = {"gsheetId": '1OE9o8OQ5P9IxhGjNKF2s9XA5ug9V__9c62W-LOHMiQQ', "worksheet_name": 'trade_log!',
                           "cell_range_insert": 'A1'}
sheet_details_candle_log = {"gsheetId": '1OE9o8OQ5P9IxhGjNKF2s9XA5ug9V__9c62W-LOHMiQQ', "worksheet_name": 'candle_log!',
                            "cell_range_insert": 'A1'}

# Telegram parameters
bot_token = '6751712468:AAE2dbimfygJ1qTxnN42JEvNmyxdGr7O6i0'
group_chat_id = '-1002113047103'
commands_active_time = 60  # in minutes
