import logging
import sys
import threading
import time
from enum import Enum
from typing import Tuple
import platform
from kiteconnect import KiteTicker, KiteConnect
import pandas as pd
from datetime import datetime, timedelta
import os
import traceback


# market time is not checked if test run is true
test_run = True
google_sheet_enabled = True
# logging.basicConfig(level=logging.DEBUG)

if not test_run and platform.system() != 'Darwin':
    sys.stdout = open('C:\\Users\\Administrator\\Downloads\\Nifty-project\\Task Scheduler Task Output logs\\output.log',
                      'a')
    sys.stderr = open('C:\\Users\\Administrator\\Downloads\\Nifty-project\\Task Scheduler Task Output logs\\error.log',
                      'a')

    sys.stdout.flush()
    sys.stderr.flush()

if platform.system() != 'Darwin':
    module_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                              'C:\\Users\\Administrator\\Downloads\\Nifty-project\\Nifty_Kite'))
    sys.path.append(module_dir)

from KiteAuto import kite_auth
from NiftY_50 import get_nifty50_tokens, get_market_timings
from fileUtls import add_line_to_file, is_file_empty, getLogStr_from_dfRow, add_line_break_to_last_line
from googleSheetUtls import initialize_google_sheet_api, add_row_to_sheet, sheetValues_from_dfRow
from Telegram_utls import send_telegram_message
from global_strings import time_s, open_s, high_s, low_s, close_s, volume_s, rsi_s, close_ma_s, volume_ma_s, gain_s, \
    loss_s, \
    avg_gain_s, avg_loss_s, rsi_ma_s
from global_strings import kite_wd, address_of_historical_candle_csv, trade_log_file, candle_today_file, \
    trade_today_file, \
    candle_log_format, trade_log_format
from global_strings import trade, gain, cumulative_gain, indicator, tgt, sl, index_s, time_format, time_formats
from global_strings import sheet_details_trade_log, sheet_details_candle_log, CLIENT_SECRET_FILE, API_SERVICE_NAME, \
    API_VERSION, SCOPES, token_file

import strategy_globals
from strategy_globals import candle_time, sma_period, rsi_period, vma_period, number_of_historical_candles_needed
from strategy_globals import close_up, close_down, rsi_up, rsi_down, stoploss_percentage, target_percentage, lot_size

# trading start and end time
start_time = None
end_time = None

# checking if kite connection happens again
connection_count = 0

# google sheet api service
service = None
log_data_frame = pd.DataFrame

# global variables for fetching Nifty 50 Companies token
instrument_tokens_nifty50 = []
Nifty50_token = 0

# dataframe for storing live data
live_data_frame = pd.DataFrame
live_index = 0

# global variables for making candles
nifty_tick = 0
nifty_tick_prev = 0
##############################
# change these three values to run from anytime
open_ = 0
volume_prev = 0
run_before_market_start_time = True
###############################
close = 0
now = None
next_candle_open_time = None
first_candle_of_current_session = True
close_done = True

# global variable for calculating volume
volume = 0
instruments_dict = {}
volume_dict_prev = {}
volume_dict_curr = {}


def on_ticks(ws, ticks):
    # Callback to receive ticks.
    global next_candle_open_time, first_candle_of_current_session, run_before_market_start_time
    global volume_dict_curr, volume_dict_prev, volume_prev
    global nifty_tick, nifty_tick_prev, start_time, end_time
    global open_, close, now, volume, close_done
    global live_data_frame, live_index, long, short

    for tick in ticks:
        if tick["instrument_token"] != Nifty50_token:
            volume_dict_curr[tick["instrument_token"]] = tick["volume_traded"]
        else:
            nifty_tick = tick["last_price"]
            now = tick["exchange_timestamp"]

    check_for_trade_exit()

    ##Make Candles
    if now >= next_candle_open_time:
        live_data_frame.loc[live_index, time_s] = next_candle_open_time - timedelta(minutes=candle_time)
        volume_curr = sum(volume_dict_curr.values())
        volume = volume_curr - volume_prev
        if not first_candle_of_current_session:
            close = nifty_tick_prev

            live_data_frame.loc[live_index, volume_s] = volume
            live_data_frame.loc[live_index, close_s] = close
            live_data_frame.loc[live_index, open_s] = open_

            calculate_indicators()

            str_log = getLogStr_from_dfRow(live_data_frame.iloc[live_index], candle_log_format)
            add_line_to_file(address_of_historical_candle_csv, str_log)

            if google_sheet_enabled:
                values = sheetValues_from_dfRow(live_data_frame.iloc[live_index], candle_log_format)
                thread_gs = threading.Thread(target=add_row_to_sheet, args=(service, values, sheet_details_candle_log))
                thread_gs.start()

        first_candle_of_current_session = False

        long, short = predict_long_short()

        if next_candle_open_time >= end_time and not test_run:
            live_data_frame.to_csv(candle_today_file, index=False)
            log_data_frame.to_csv(trade_today_file, index=False)
            exit_time = datetime.now()
            send_telegram_message("Program stopped properly at time " + str(exit_time))
            ws.stop()
            exit()

        # trading conditions here
        check_for_trade_entry()

        ##next candle
        live_index = live_index + 1

        if run_before_market_start_time:
            open_ = nifty_tick
            volume_prev = volume_curr
        run_before_market_start_time = True
        next_candle_open_time = next_candle_open_time + timedelta(minutes=candle_time)

    if nifty_tick != 0:
        nifty_tick_prev = nifty_tick


def calculate_indicators():
    global close, live_data_frame, live_index, volume
    # get loss and gain
    temp_t = close - live_data_frame.loc[live_index - 1, close_s]

    # set loss and gain
    if temp_t > 0:
        live_data_frame.loc[live_index, gain_s] = temp_t
        live_data_frame.loc[live_index, loss_s] = 0
    else:
        live_data_frame.loc[live_index, gain_s] = 0
        live_data_frame.loc[live_index, loss_s] = -temp_t

    # set average gain and loss
    live_data_frame.loc[live_index, avg_gain_s] \
        = (live_data_frame.loc[live_index - 1, avg_gain_s] * (rsi_period - 1) +
           live_data_frame.loc[live_index, gain_s]) / rsi_period
    live_data_frame.loc[live_index, avg_loss_s] \
        = (live_data_frame.loc[live_index - 1, avg_loss_s] * (rsi_period - 1) +
           live_data_frame.loc[live_index, loss_s]) / rsi_period

    # set rsi
    live_data_frame.loc[live_index, rsi_s] = \
        100 - 100 / (1 + (live_data_frame.loc[live_index, avg_gain_s]
                          / live_data_frame.loc[live_index, avg_loss_s]))

    # set close moving average
    live_data_frame.loc[live_index, close_ma_s] \
        = (live_data_frame.loc[live_index - 1, close_ma_s]
           * sma_period - live_data_frame.loc[live_index - sma_period, close_s] + close) / sma_period

    # set volume moving average
    live_data_frame.loc[live_index, volume_ma_s] \
        = (live_data_frame.loc[live_index - 1, volume_ma_s]
           * vma_period - live_data_frame.loc[live_index - vma_period, volume_s] + volume) / vma_period


##global variables for prediction
class Trade(Enum):
    LONG_POSITION = "long"
    SHORT_POSITION = "short"
    NONE = "none"


long = False
short = False


def predict_long_short() -> Tuple[bool, bool]:
    global live_data_frame, live_index
    crossover_close = False
    crossunder_close = False
    green_candle = False
    red_candle = False
    rsi_long = False
    rsi_short = False
    # predict long short
    if live_data_frame.loc[live_index, volume_s] > live_data_frame.loc[live_index, volume_ma_s]:
        green_candle = live_data_frame.loc[live_index, close_s] \
                       > live_data_frame.loc[live_index, open_s]
        red_candle = live_data_frame.loc[live_index, close_s] \
                     < live_data_frame.loc[live_index, open_s]
        crossover_close = live_data_frame.loc[live_index, close_s] > \
                          live_data_frame.loc[live_index, close_ma_s] * (1 + (close_up / 100)) and \
                          live_data_frame.loc[live_index - 1, close_s] < \
                          live_data_frame.loc[live_index - 1, close_ma_s] * (1 + (close_up / 100))
        crossunder_close = live_data_frame.loc[live_index, close_s] < \
                           live_data_frame.loc[live_index, close_ma_s] * (1 - (close_down / 100)) and \
                           live_data_frame.loc[live_index - 1, close_s] > \
                           live_data_frame.loc[live_index - 1, close_ma_s] * (1 - (close_down / 100))

        rsi_long = live_data_frame.loc[live_index, rsi_s] > rsi_up
        rsi_short = live_data_frame.loc[live_index, rsi_s] < rsi_down

    long_ = green_candle and crossover_close and rsi_long
    short_ = red_candle and crossunder_close and rsi_short

    return long_, short_


trade_type = Trade.NONE
stoploss = 0
target = 0
entry_index = 0
cumulative_profit = 0
log_index = 0
in_trade = False


def check_for_trade_entry():
    global trade_type, in_trade, long, short, log_index, log_data_frame
    global stoploss, target, entry_index
    global nifty_tick, now, cumulative_profit

    trade_entry = False

    if long:
        trade_entry = True
        stoploss = nifty_tick * (1 - (stoploss_percentage / 100))
        target = nifty_tick * (1 + (target_percentage / 100))
        trade_type = Trade.LONG_POSITION

        log_data_frame.loc[log_index, indicator] = "long"

    elif short:
        trade_entry = True
        stoploss = nifty_tick * (1 + (stoploss_percentage / 100))
        target = nifty_tick * (1 - (target_percentage / 100))
        trade_type = Trade.SHORT_POSITION

        log_data_frame.loc[log_index, indicator] = "short"

    if trade_entry:
        log_data_frame.loc[log_index, time_s] = now
        log_data_frame.loc[log_index, index_s] = nifty_tick
        log_data_frame.loc[log_index, tgt] = target
        log_data_frame.loc[log_index, sl] = stoploss
        log_data_frame.loc[log_index, cumulative_gain] = cumulative_profit

        if in_trade:
            log_data_frame.loc[log_index, trade] = "reset tgt/sl"
        else:
            entry_index = nifty_tick
            log_data_frame.loc[log_index, trade] = "entry"

        str_log = getLogStr_from_dfRow(log_data_frame.iloc[log_index], trade_log_format)
        add_line_to_file(trade_log_file, str_log)

        if google_sheet_enabled:
            values = sheetValues_from_dfRow(log_data_frame.iloc[log_index], trade_log_format)
            thread_gs = threading.Thread(target=add_row_to_sheet, args=(service, values, sheet_details_trade_log))
            thread_gs.start()

        log_index = log_index + 1
        in_trade = True


def check_for_trade_exit():
    global in_trade, trade_type, cumulative_profit, log_index, log_data_frame, entry_index
    global stoploss, target
    global nifty_tick, now

    trade_exit = False
    profit_multiplier = 1  # will set to -1 in case of short trade

    if in_trade:
        if trade_type == Trade.LONG_POSITION:
            if nifty_tick >= target:
                trade_exit = True
                log_data_frame.loc[log_index, indicator] = "achieved target"
            elif nifty_tick <= stoploss:
                trade_exit = True
                log_data_frame.loc[log_index, indicator] = "reached stoploss"

        elif trade_type == Trade.SHORT_POSITION:
            profit_multiplier = -1
            if nifty_tick <= target:
                trade_exit = True
                log_data_frame.loc[log_index, indicator] = "achieved target"
            elif nifty_tick >= stoploss:
                trade_exit = True
                log_data_frame.loc[log_index, indicator] = "reached stoploss"

    if trade_exit:
        log_data_frame.loc[log_index, time_s] = now
        log_data_frame.loc[log_index, index_s] = nifty_tick
        log_data_frame.loc[log_index, trade] = "exit"

        profit = lot_size * (nifty_tick - entry_index) * profit_multiplier
        cumulative_profit = cumulative_profit + profit
        log_data_frame.loc[log_index, gain] = profit
        log_data_frame.loc[log_index, cumulative_gain] = cumulative_profit

        str_log = getLogStr_from_dfRow(log_data_frame.iloc[log_index], trade_log_format)
        add_line_to_file(trade_log_file, str_log)

        if google_sheet_enabled:
            values = sheetValues_from_dfRow(log_data_frame.iloc[log_index], trade_log_format)
            thread_gs = threading.Thread(target=add_row_to_sheet, args=(service, values, sheet_details_trade_log))
            thread_gs.start()

        log_index = log_index + 1
        in_trade = False


def initialize_df_with_historical_data():
    global live_data_frame
    global live_index, run_before_market_start_time
    global nifty_tick_prev, next_candle_open_time, open_, volume_prev

    historical_data_frame = pd.read_csv(address_of_historical_candle_csv, skip_blank_lines=True)

    # Additional code for running code when market iss already open for some time
    # ----------------- START -------------------------#
    current_time = datetime.now()
    if current_time <= start_time:
        next_candle_open_time = start_time
        run_before_market_start_time = True
    else:
        time_diff = (current_time.minute - start_time.minute) % candle_time
        next_candle_open_time = (current_time - timedelta(hours=0, minutes=time_diff)).replace(second=0, microsecond=0)
        run_before_market_start_time = False
        print(next_candle_open_time)

    if not run_before_market_start_time:
        if open_ == 0:
            last_index = historical_data_frame.__len__() - 1
            for time_fmt in time_formats:
                try:
                    last_candle_time = datetime.strptime(historical_data_frame.loc[last_index, time_s][:19], time_fmt)
                    break  # Stop looping if parsing succeeds
                except ValueError:
                    print(traceback.format_exc())
                    continue  # Try the next format if parsing fails
            if last_candle_time == next_candle_open_time:
                open_ = historical_data_frame.loc[last_index, open_s]
                historical_data_frame.drop(historical_data_frame.index[-1], inplace=True)
            else:
                open_ = historical_data_frame.loc[last_index, close_s]
        if volume_prev == 0:
            start_index = historical_data_frame.__len__() - 1
            today = current_time.date()
            for index_d in range(start_index, 0, -1):
                for time_fmt in time_formats:
                    try:
                        candle_date = datetime.strptime(historical_data_frame.loc[index_d, time_s][:19],
                                                        time_fmt).date()
                        break  # Stop looping if parsing succeeds
                    except ValueError:
                        print(traceback.format_exc())
                        continue  # Try the next format if parsing fails
                if candle_date != today:
                    break
                else:
                    volume_prev = volume_prev + historical_data_frame.loc[index_d, volume_s]

    historical_data_frame.to_csv(address_of_historical_candle_csv, index=False)
    add_line_break_to_last_line(address_of_historical_candle_csv)
    # ----------------- END -------------------------#

    historical_data_required_to_calculate_ma = (
        historical_data_frame.tail(number_of_historical_candles_needed)).reset_index()

    no_of_historical_candles = historical_data_required_to_calculate_ma.__len__()

    i = 0
    for i in range(0, no_of_historical_candles):
        live_data_frame.loc[i, open_s] = historical_data_required_to_calculate_ma[open_s][i]
        live_data_frame.loc[i, close_s] = historical_data_required_to_calculate_ma[close_s][i]
        live_data_frame.loc[i, volume_s] = historical_data_required_to_calculate_ma[volume_s][i]
        live_data_frame.loc[i, time_s] = historical_data_required_to_calculate_ma[time_s][i]
        live_data_frame.loc[i, rsi_s] = historical_data_required_to_calculate_ma[rsi_s][i]

    # calculate volume ma
    live_data_frame.loc[i, volume_ma_s] = live_data_frame.loc[no_of_historical_candles - vma_period:
                                                              no_of_historical_candles, volume_s].sum() / vma_period

    # calculate close ma
    live_data_frame.loc[i, close_ma_s] = live_data_frame.loc[no_of_historical_candles - sma_period:
                                                             no_of_historical_candles, close_s].sum() / sma_period

    # calculate rsi
    ##calculate average gain and average loss

    temp = live_data_frame.loc[no_of_historical_candles - 1, close_s] \
           - live_data_frame.loc[no_of_historical_candles - 2, close_s]
    c_g = 0  # current gain
    c_l = 0  # current loss
    if temp > 0:
        c_g = temp
    else:
        c_l = -temp
    r2 = live_data_frame.loc[no_of_historical_candles - 1, rsi_s]  # current rsi
    r1 = live_data_frame.loc[no_of_historical_candles - 2, rsi_s]  # previous rsi

    rs2 = (100 / (100 - r2)) - 1
    rs1 = (100 / (100 - r1)) - 1

    average_loss = (c_g - rs2 * c_l) / (rs2 - rs1)
    average_loss = average_loss / (rsi_period - 1)
    average_gain = rs1 * average_loss

    average_gain = (average_gain * (rsi_period - 1) + c_g) / rsi_period
    average_loss = (average_loss * (rsi_period - 1) + c_l) / rsi_period

    live_data_frame.loc[no_of_historical_candles - 1, avg_gain_s] = average_gain
    live_data_frame.loc[no_of_historical_candles - 1, avg_loss_s] = average_loss

    live_index = no_of_historical_candles - 1

    nifty_tick_prev = historical_data_required_to_calculate_ma[close_s][i]


def on_connect(ws, response):
    global Nifty50_token, connection_count
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe(instrument_tokens_nifty50)
    ws.subscribe([int(Nifty50_token)])
    ws.set_mode(ws.MODE_FULL, [Nifty50_token])

    connection_count = connection_count + 1
    print("connected(" + str(connection_count) + ") to kite now")

    if not test_run:
        current_time = datetime.now()
        time_difference_seconds = (start_time - current_time).total_seconds()
        if time_difference_seconds > 0:
            print(f"Waiting for {time_difference_seconds - 1} seconds...")
            time.sleep(time_difference_seconds - 1)
            print("Time is now " + str(datetime.now()))
        else:
            print("Time is now " + str(datetime.now()))
    print("")
    send_telegram_message("Ticks started at time " + str(datetime.now()))
    print("----------------------------------Starting ticks----------------------------------")

    # Set RELIANCE to tick in `full` mode.
    # ws.set_mode(ws.MODE_FULL, [738561,12670978])


def on_error(self, ws, reason):
    print("Error Code: ")


def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    live_data_frame.to_csv(candle_today_file, index=False)
    log_data_frame.to_csv(trade_today_file, index=False)
    exit_time = datetime.now()
    send_telegram_message("Program stopped at time " + str(exit_time))
    # ws.stop()


def main():
    global volume_dict_prev, volume_dict_curr, start_time, end_time
    global instruments_dict, instrument_tokens_nifty50, Nifty50_token
    global live_data_frame, log_data_frame, service
    global in_trade, trade_type, cumulative_profit, log_data_frame, entry_index, stoploss, target, \
        nifty_tick, now

    # check if market is open
    if not test_run:
        start_time, end_time = get_market_timings()
        if start_time == False:
            send_telegram_message(end_time)
            exit()
        if datetime.now() > end_time:
            print("NSE is closed now")
            send_telegram_message("NSE is closed now")
            exit()
    else:
        start_time, end_time = strategy_globals.start_time, strategy_globals.end_time

    # dataframe for storing candles
    live_data_frame = pd.DataFrame(columns=[time_s, open_s, high_s, low_s, close_s, volume_s, close_ma_s, volume_ma_s,
                                            gain_s, loss_s, avg_gain_s, avg_loss_s, rsi_s, rsi_ma_s],
                                   index=range(0, number_of_historical_candles_needed + 12 * 7))

    # dataframe for registering trade
    log_data_frame = pd.DataFrame(columns=trade_log_format,
                                  index=range(0, 50))

    ##initialize google sheet api and set last trade values
    if google_sheet_enabled:
        service = initialize_google_sheet_api(CLIENT_SECRET_FILE, SCOPES, API_SERVICE_NAME, API_VERSION, token_file)
    if is_file_empty(trade_log_file):
        log_columns_str = ",".join(trade_log_format)
        add_line_to_file(trade_log_file, log_columns_str)
    else:
        temp_log_df = pd.read_csv(trade_log_file, skip_blank_lines=True)
        add_line_break_to_last_line(trade_log_file)
        # add_dataframe_to_sheet(service, temp_log_df, sheet_details, trade_log_format)
        if temp_log_df.__len__() > 0:
            if temp_log_df[trade].iloc[-1] == "entry" or temp_log_df[trade].iloc[-1] == "reset tgt/sl":
                in_trade = True
                trade_type = temp_log_df[indicator].iloc[-1]
                stoploss = float(temp_log_df[sl].iloc[-1])
                target = float(temp_log_df[tgt].iloc[-1])
                entry_index = float(temp_log_df[index_s].iloc[-1])
            cumulative_profit = float(temp_log_df[cumulative_gain].iloc[-1])


    ##initialize kite api
    kite, api_key, access_token = kite_auth(kite_wd)
    #kite.debug = True


    ##get current instruments and save in dataframe
    instrument_tokens_nifty50, symbols_nifty50, Nifty50_token = get_nifty50_tokens(kite)

    # dictionary containing tokens and symbols
    instruments_dict = dict(zip(instrument_tokens_nifty50, symbols_nifty50))

    # dictionary for saving volume
    volume_dict_prev = dict.fromkeys(instrument_tokens_nifty50, 0)
    volume_dict_curr = dict.fromkeys(instrument_tokens_nifty50, None)

    # initialize strategy df with previous day candle data
    initialize_df_with_historical_data()

    kws = KiteTicker(api_key, access_token)

    kws.on_ticks = on_ticks
    kws.on_connect = on_connect
    kws.on_close = on_close

    thread = threading.Thread(target=kws.connect())
    thread.start()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Exception in main()\n" + e.__str__())
        print(traceback.format_exc())

