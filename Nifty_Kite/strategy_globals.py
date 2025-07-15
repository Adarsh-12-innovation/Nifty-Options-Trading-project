from datetime import datetime


##global variables for strategy
close_up = 0.1
close_down = 0.1
rsi_up = 65
rsi_down = 35
stoploss_percentage = 0.1
target_percentage = 0.2
lot_size = 50

##global variables for processing tick data
candle_time = 5  # in minutes
sma_period = 10  # simple moving average, previous 10 candles
rsi_period = 14  # relative strength indicator, previous 14 candles
vma_period = 20  # moving average of traded volume, previous 20 candles
number_of_historical_candles_needed = int(max(sma_period, rsi_period, vma_period))  # maximum of above 3
start_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)
end_time = datetime.now().replace(hour=15, minute=30, second=0, microsecond=0)

