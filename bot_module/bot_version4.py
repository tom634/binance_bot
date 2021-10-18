import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *
import time, datetime
import pandas as pd
from datetime import datetime, timedelta

# import Constants


SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"
TRADE_SYMBOL = 'BTCUSDT'
TRADE_SYMBOL_HISTORY = 'BTCUSDT'



# RSI_PERIOD = 14
# RSI_OVERBOUGHT = 70
# RSI_OVERSOLD = 30
TRADE_QUANTITY = 0.006
flag=True
prediction=False
# sell_locations=[]
# buy_locations=[]
# position=False
# money=500
# current_eth=0
# money_array=[]

# closes = []
position = False
money=200
current_crypto=0
money_array=[]

# def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
#     try:
#         # print("Placing an order...")
#         f = open( 'transactions.txt', 'a' )
#         order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
#         # print(order)
#         if order['side']=='BUY':
#             amount_bought=order['cummulativeQuoteQty']
#             print(order['symbol'],"\t",order['side'],"\t",round(-float(amount_bought),3),"\t",datetime.utcfromtimestamp(order['transactTime']/1000).strftime('%Y-%m-%d %H:%M:%S'))
#             f.write(order['symbol']+'\t'+order['side']+'\t'+str(round(-float(amount_bought),3))+'\t'+datetime.utcfromtimestamp(order['transactTime']/1000).strftime('%Y-%m-%d %H:%M:%S')+'\n')
#         else:
#             print(order['symbol'],"\t",order['side'],"\t",round(float(order['cummulativeQuoteQty']),3),"\t",datetime.utcfromtimestamp(order['transactTime']/1000).strftime('%Y-%m-%d %H:%M:%S'))
#             f.write(order['symbol']+'\t'+order['side']+'\t'+str(round(float(order['cummulativeQuoteQty']),3))+'\t'+datetime.utcfromtimestamp(order['transactTime']/1000).strftime('%Y-%m-%d %H:%M:%S')+'\n')
#         f.close() 
#     except Exception as e:
#         print("An exception occured - {}".format(e))
#         return False

#     return True

def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
    print("Placing an order...")
    return True

    
def on_open(ws):
    print('Connection established! Listening to messages...')

def on_close(ws):
    print('Connection closed!')

def on_message(ws, message):
    global position, df, df_temp, flag, prediction, money, current_crypto, money_array

    global position
    # print("ON MESSAGE DF\n", df.tail(5))
    # print('received message')
    json_message = json.loads(message)
    
    

    # MESSAGE STRUCTURE: https://python-binance.readthedocs.io/en/latest/binance.html#module-binance.streams
    # {
    # "e": "kline",                           # event type
    # "E": 1499404907056,                     # event time
    # "s": "ETHBTC",                          # symbol
    # "k": {
    #     "t": 1499404860000,                 # start time of this bar
    #     "T": 1499404919999,                 # end time of this bar
    #     "s": "ETHBTC",                      # symbol
    #     "i": "1m",                          # interval
    #     "f": 77462,                         # first trade id
    #     "L": 77465,                         # last trade id
    #     "o": "0.10278577",                  # open
    #     "c": "0.10278645",                  # close
    #     "h": "0.10278712",                  # high
    #     "l": "0.10278518",                  # low
    #     "v": "17.47929838",                 # volume
    #     "n": 4,                             # number of trades
    #     "x": false,                         # whether this bar is final
    #     "q": "1.79662878",                  # quote volume
    #     "V": "2.34879839",                  # volume of active buy
    #     "Q": "0.24142166",                  # quote volume of active buy
    #     "B": "13279784.01349473"            # can be ignored
    #     }
    # }


    # pprint.pprint(json_message)
    candle = json_message['k']

    # local_time=candle['t']
    current_time = datetime.now()
    # check if currently is 30 seconds before closing the current candle...
    current_open = candle['o']
    current_price = candle['c']
    current_high = candle['h']
    current_low = candle['l']
    # print("current price", current_price, "low:", current_low, "high", current_high, "current open", current_open)
    is_candle_closed = candle['x']
    if is_candle_closed:
        df = df.append({'closeTime': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'close': candle['c'], 'open': candle['o'], 'high' : candle['h'], "low": candle['l'], 'volume': candle['v']}, ignore_index=True)
        # print("candle closed! Verify if prediction was good!")
        ma_2 = talib.SMA(df.close, timeperiod=2)
        ma_3 = talib.SMA(df.close, timeperiod=3)
        ma_4 = talib.SMA(df.close, timeperiod=4)

        df['ma_2']=ma_2
        df['ma_3']=ma_3
        df['ma_4']=ma_4
        # print("DF TAIL ON CLOSE:\n", df.tail(3))
        if (df['ma_2'].iloc[-1]>df['ma_4'].iloc[-1]) & (df['ma_3'].iloc[-1]>df['ma_4'].iloc[-1]) & (df['ma_2'].iloc[-1]>df['ma_3'].iloc[-1]):
            if prediction==True:
                print("Prediction was good! It went up! We are at position, so doing nothing...")
                with open("prediction.txt", "a") as myfile:
                    myfile.write("GOOD"+'\n')


            else:
                print("Prediction was bad! It went down! Panic selling!")
                if position==True:
                    with open("prediction.txt", "a") as myfile:
                        myfile.write("BAD"+'\n')

                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        position = False

                    money+=current_crypto*float(df['close'].iloc[-1])-0.2
                    current_crypto=0
                    money_array.append(money)
                    print("Time:",df['closeTime'].iloc[-1],"price",df['close'].iloc[-1],"money:", money)
                    with open("money.txt", "a") as myfile:
                        myfile.write(df['closeTime'].iloc[-1]+'\t'+df['close'].iloc[-1]+'\t'+str(money)+'\n')
                else:
                    print("No need to panic sell!")

        else:
            if prediction==False:
                print("Prediction was good! It didn't go up!!")
                with open("prediction.txt", "a") as myfile:
                    myfile.write("GOOD"+'\n')
            else:
                print("Prediction was bad! It went up! Panic buying!")
                if position==False:
                    # put binance buy order logic here
                    print(df['closeTime'].iloc[-1],"Buying...")
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        position = True

                    money-=200.2
                    current_crypto=199.8/float(df['close'].iloc[-1])
                    money_array.append(money)
                    print("Time:",df['closeTime'].iloc[-1],"price",df['close'].iloc[-1],"money:", money)


                    with open("prediction.txt", "a") as myfile:
                        myfile.write("BAD"+'\n')
                    with open("money.txt", "a") as myfile:
                        myfile.write(df['closeTime'].iloc[-1]+'\t'+df['close'].iloc[-1]+'\t'+str(money)+'\n')
                else:
                    print("No need to panic buy!")

        flag=True
    else:
        if (datetime.utcnow()>datetime.utcfromtimestamp(candle['T']/1000)-timedelta(seconds = 15)) & flag==True:
            # print("current:",datetime.now())
            # print("Candle", datetime.utcfromtimestamp(candle['T']/1000)-timedelta(seconds = 30))
            # print("now is 30 seconds after!")
            # print("TYPE:", type(candle['T']))

            df_temp = df.append({'closeTime': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'close': candle['c'], 'open': candle['o'], 'high' : candle['h'], "low": candle['l'], 'volume': candle['v']}, ignore_index=True)
            # print("DF_TEMP:\n",df_temp.tail(3))
            ma_2 = talib.SMA(df_temp.close, timeperiod=2)
            ma_3 = talib.SMA(df_temp.close, timeperiod=3)
            ma_4 = talib.SMA(df_temp.close, timeperiod=4)

            df_temp['ma_2']=ma_2
            df_temp['ma_3']=ma_3
            df_temp['ma_4']=ma_4
            # print("DF_TEMP:\n",df_temp.tail(3))
            # print("DF_LOL:\n",df.tail(3))
            if (df_temp['ma_2'].iloc[-1]>df_temp['ma_4'].iloc[-1]) & (df_temp['ma_3'].iloc[-1]>df_temp['ma_4'].iloc[-1]) & (df_temp['ma_2'].iloc[-1]>df_temp['ma_3'].iloc[-1]):
                print("I predict growth! Checking additional criteria...")
                if df_temp['ma_2'].iloc[-1]>df['ma_2'].iloc[-1]:
                    if position==False:
                        print("I predict growth! Buying...")
                        # put binance buy order logic here
                        print(df_temp['closeTime'].iloc[-1],"Buying...")
                        order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            position = True

                        money-=200.2
                        current_crypto=199.8/float(df_temp['close'].iloc[-1])
                        money_array.append(money)
                        print("Time:",df_temp['closeTime'].iloc[-1],"price",df_temp['close'].iloc[-1],"money:", money)
                        with open("money.txt", "a") as myfile:
                            myfile.write(df_temp['closeTime'].iloc[-1]+'\t'+df_temp['close'].iloc[-1]+'\t'+str(money)+'\n')


                        prediction=True
                    else:
                        print("We are holding since it is going up!")
                        prediction=True
                else:
                    if position==True:
                        print(df_temp['closeTime'].iloc[-1],"We are at inflection point, selling...")
                        # put binance sell logic here
                        order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            position = False
                        prediction = False

                        money+=current_crypto*float(df_temp['close'].iloc[-1])-0.2
                        current_crypto=0
                        money_array.append(money)
                        print("Time:",df_temp['closeTime'].iloc[-1],"price",df_temp['close'].iloc[-1],"money:", money)
                        with open("money.txt", "a") as myfile:
                            myfile.write(df_temp['closeTime'].iloc[-1]+'\t'+df_temp['close'].iloc[-1]+'\t'+str(money)+'\n')
            else:
                print("I don't predict growth!")
                prediction=False
                if position==True:
                    # print(df_temp['closeTime'].iloc[-1],"Selling!")
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        position = False

                    money+=current_crypto*float(df_temp['close'].iloc[-1])-0.2
                    current_crypto=0
                    money_array.append(money)
                    print("Time:",df_temp['closeTime'].iloc[-1],"price",df_temp['close'].iloc[-1],"money:", money)
                    with open("money.txt", "a") as myfile:
                        myfile.write(df['closeTime'].iloc[-1]+'\t'+df_temp['close'].iloc[-1]+'\t'+str(money)+'\n')
                else:
                    pass
                    # print("we are not in the position, doing nothing!")
            flag=False

            
    # break
    # else:
    #     is_candle_closed = candle['x']
    #     print("NOT CLOSED!")
    #     flag=False
        
        # is_candle_closed=False
        # else:
        #     print("CLOSED")
            
    # local_time=local_time/1000
    # print('Read', candle['s'], "at:", datetime.utcfromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S') ,'price',candle['c'])
            # print("CANDLE CLOSED?", candle['x'])
            # is_candle_closed = candle['x']
            # close = candle['c']
            
            # if wait_until(is_candle_closed)==True:
            #     print("continue")
        
        

        # if len(closes) > RSI_PERIOD:
        #     np_closes = numpy.array(closes)
        #     rsi = talib.RSI(np_closes, RSI_PERIOD)
        #     print("all rsis calculated so far")
        #     print(rsi)
        #     last_rsi = rsi[-1]
        #     print("the current rsi is {}".format(last_rsi))

        #     if last_rsi > RSI_OVERBOUGHT:
        #         if in_position:
        #             print("Overbought! Sell! Sell! Sell!")
        #             # put binance sell logic here
        #             order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
        #             if order_succeeded:
        #                 in_position = False
        #         else:
        #             print("It is overbought, but we don't own any. Nothing to do.")
            
        #     if last_rsi < RSI_OVERSOLD:
        #         if in_position:
        #             print("It is oversold, but you already own it, nothing to do.")
        #         else:
        #             print("Oversold! Buy! Buy! Buy!")
        #             # put binance buy order logic here
        #             order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
        #             if order_succeeded:
        #                 in_position = True


print("Launching script...")

def GetHistoricalData(howLong):
    howLong = howLong
    # Calculate the timestamps for the binance api function
    untilThisDate = datetime.now()
    # sinceThisDate = untilThisDate - datetime.timedelta(days = howLong)
    sinceThisDate = untilThisDate - timedelta(hours = howLong)
    # Execute the query from binance - timestamps must be converted to strings !
    candle = client.get_historical_klines(TRADE_SYMBOL_HISTORY, Client.KLINE_INTERVAL_1MINUTE, str(sinceThisDate), str(untilThisDate))
    # print("TYPE", type(candle),"\n",candle)

    # Create a dataframe to label all the columns returned by binance so we work with them later.
    df = pd.DataFrame(candle, columns=['dateTime', 'open', 'high', 'low', 'close', 'volume', 'closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol', 'takerBuyQuoteVol', 'ignore'])
    # as timestamp is returned in ms, let us convert this back to proper timestamps.
    # df.dateTime = pd.to_datetime(df.dateTime, unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
    # df.set_index('dateTime', inplace=True)

    # Get rid of columns we do not need
    df = df.drop(['dateTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol','takerBuyQuoteVol', 'ignore'], axis=1)

    return df

client = Client(config.API_KEY, config.API_SECRET)#, tld='us')

# info = client.get_symbol_info(TRADE_SYMBOL)
prices = client.get_all_tickers()
print(prices)
# print("INFO",info)
df=GetHistoricalData(3) # TAKE INTO ACCOUNT GMT-2

print("LOADED AT FIRST\n", df)

# df = df.sort_values(by='dateTime')
df.closeTime = pd.to_datetime(df.closeTime, unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
# df.dateTime = pd.to_datetime(df.dateTime, unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
# df=df.reset_index(drop=True)

ma_2 = talib.SMA(df.close, timeperiod=2)
ma_3 = talib.SMA(df.close, timeperiod=3)
ma_4 = talib.SMA(df.close, timeperiod=4)

df['ma_2']=ma_2
df['ma_3']=ma_3
df['ma_4']=ma_4

print("Loaded dataframe\n",df)

client = Client(config.API_KEY, config.API_SECRET)#, tld='us')
df_temp = df
print("Data loaded!")
# time.sleep(10)
print("1...we are here")

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)



print("2...we are here")
ws.run_forever()
