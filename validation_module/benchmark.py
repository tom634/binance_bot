#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This Python script benchmarkes approaches

"""
from binance.client import Client
from binance.enums import *
import config
import numpy as np
import pandas as pd
import time
from scipy.signal import butter, lfilter
import matplotlib.pyplot as plt
import os
import scipy
from sys import getsizeof
import glob
import talib
from datetime import datetime, timedelta

print("Binance crypto trading bot\n")

TRADE_SYMBOL_HISTORY = 'BTCUSDT'

columns_to_drop=['quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore']
print("In order to reduce consumption of RAM memory, it is possible to drop unnecesary columns.")
print("Selected columns to drop are:\n", columns_to_drop)
print("Multiple CSV files will be loaded...")


def GetHistoricalData(howLong):
    howLong = howLong
    # Calculate the timestamps for the binance api function
    untilThisDate = datetime.now()
    sinceThisDate = untilThisDate - timedelta(days = howLong)
    # Execute the query from binance - timestamps must be converted to strings !
    candle = client.get_historical_klines(TRADE_SYMBOL_HISTORY, Client.KLINE_INTERVAL_5MINUTE, str(sinceThisDate), str(untilThisDate))
    # Create a dataframe to label all the columns returned by binance so we work with them later.
    df = pd.DataFrame(candle, columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])
    # Get rid of columns we do not need
    df = df.drop(['dateTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol','takerBuyQuoteVol', 'ignore'], axis=1)
    return df

client = Client(config.API_KEY, config.API_SECRET)#, tld='us')

# print info about available tokens:
# info = client.get_symbol_info(TRADE_SYMBOL)
# prices = client.get_all_tickers()
# print(prices)
# print("INFO",info)

print("Downloading historical data...")
df=GetHistoricalData(7) # TAKE INTO ACCOUNT GMT-2!
# convert closetime to datetime format
df.closeTime = pd.to_datetime(df.closeTime, unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
print("LOADED AT FIRST\n", df)
df['open'] = df['open'].astype(float)
df['close'] = df['close'].astype(float)

# calculate last and first price to compare with HODL
last_price=float(df.at[len(df)-1,'close'])
first_price=float(df.at[0,'close'])

# print loaded data...
# print("PANDAS DATAFRAME\n",df)

# ma_18 = talib.SMA(df.close, timeperiod=18)
# ma_22 = talib.SMA(df.close, timeperiod=22)
# ma_200 = talib.SMA(df.close, timeperiod=200)

ma_2 = talib.SMA(df.close, timeperiod=5)
ma_3 = talib.SMA(df.close, timeperiod=8)
ma_4 = talib.SMA(df.close, timeperiod=13)

df['ma_2']=ma_2
df['ma_3']=ma_3
df['ma_4']=ma_4


# plt.plot(df.index,df['open'],label='Open')
# plt.plot(df.index,ma_2,label='MA2', color='g')
# plt.plot(df.index,ma_3,label='MA3', color='r')
# plt.plot(df.index,ma_4,label='MA4', color='y')
# plt.plot(df.index,df['ma_4'],label='MA200', color='k')

# calculated dataframe
# print("Calculated dataframe:\n",df)
df_length=len(df)

sell_locations=[]
buy_locations=[]
position=False
initial_money=350
money=initial_money # initial money
trade_amount=100
current_crypto=0
money_array=[]

for index, row in df.iterrows():

    if index-1<0:
        pass
    else:
        # print(index,"Current open",df.at[index,'open'])
        # print(index, "Current close",df.at[index-1,'close'])
        # print("at", df.at[index-1, 'ma_2'])
        if index%1000==1:
            print(index/df_length*100,"%, money:", money)
        if (df.at[index-1, 'ma_2']> df.at[index-1, 'ma_4']) & ( df.at[index-1, 'ma_3']> df.at[index-1, 'ma_4']):
            if df.at[index-1, 'ma_2']> df.at[index-1, 'ma_3']:
                # print("We are at upward trend, check additional criteria!", index)
                if df.at[index-1,'ma_2']>df.at[index-2,'ma_2']:
                    # print("BUY AND HOLD!", index)
                    if position==False:
                        position=True
                        buy_locations.append([index, df.at[index,'open']])
                        money-=initial_money+0.2
                        print(index,"BUY",money)
                        current_crypto=349.8/df.at[index,'open']#-0.001*200/df.at[index,'open']
                        # print(index,"open1", df.at[index,'open'])
                        # print(index-1,"close1", df.at[index-1,'close'])
                        money_array.append(money)
                    else:
                        pass
                        # print("HOLD AND GROW")
                else:
                    # CHANGE TREND RULE
                    # pass
                    # print("It is time to sell!", index)
                    if position==True:
                        position=False
                        sell_locations.append([index, df.at[index,'open']])
                        # print(money)
                        money+=current_crypto*df.at[index,'open']-0.2#current_crypto*df.at[index,'open']*0.001
                        print("SELL",money)
                        # print(index-1,"open1", df.at[index-1,'open'])
                        # print(index-1,"close1", df.at[index-1,'close'])
                        current_crypto=0
                        money_array.append(money)
                    else:
                        position=False
                        # print("Bad position, wait")
            else:
                if position==True:
                    position=False
                    sell_locations.append([index, df.at[index,'open']])
                    money+=current_crypto*df.at[index,'open']-0.2#current_crypto*df.at[index,'open']*0.001
                    # print("SELL=======",money)
                    # print(index-1,"open2", df.at[index-1,'open'])
                    # print(index-1,"close2", df.at[index-1,'close'])
                    # print(index,"open2", df.at[index,'open'])
                    # print(index,"close2", df.at[index,'close'])
                    print("SELL",money)
                    current_crypto=0
                    money_array.append(money)
                    # print("PANIC SELL!", index)
                else:
                    # print("We are at MA22 downward trend, sell and don't buy!")
                    position=False
        else:
            # print("We are at MA200 downward trend! Sell and don't buy!")
            if position==True:
                sell_locations.append([index, df.at[index,'open']])
                money+=current_crypto*df.at[index,'open']-0.2#current_crypto*df.at[index,'open']*0.001
                print("SELL",money)
                # print(index,"open3", df.at[index,'open'])
                # print(index-1,"close3", df.at[index-1,'close'])
                current_crypto=0
                position=False
                money_array.append(money)
            else:
                position=False
        # time.sleep(1)


print(buy_locations)
# for xc in buy_locations:
#     plt.axvline(x=xc, color='g')

# for xc in sell_locations:
#     plt.axvline(x=xc, color='r')
plt.scatter(*zip(*buy_locations), c='g', marker='^')
plt.scatter(*zip(*sell_locations), c='r', marker='v')

plt.plot(df.index,df['open'],label='Open', color='k')
plt.plot(df.index,ma_2,label='MA2', color='g')
plt.plot(df.index,ma_3,label='MA3', color='r')
plt.plot(df.index,ma_4,label='MA4', color='y')
plt.legend()
plt.show()
print("Writing to file:")
with open('money_array.txt', 'w') as f:
    for item in money_array:
        f.write("%s\n" % item)

print("Current_money", money)
print("HOLD:",initial_money*(last_price/first_price))
exit()