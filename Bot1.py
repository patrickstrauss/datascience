#!/usr/bin/env python
# coding: utf-8

# In[1]:


import settrade.openapi
from settrade.openapi import Investor
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pandasql import sqldf
import sys
import math


# In[2]:


##Login to Sandbox mode
investor = Investor(
                app_id="XoBfocVqAVjcCW60",                                 # Your app ID
                app_secret="RhF+aTawun2pPBivTesYb9ENMuv+E9zvnj3umyMjM0E=", # Your app Secret
                broker_id="SANDBOX",                                           
                app_code="SANDBOX",
                is_auto_queue = False)


# In[3]:


#equity for placing orders
eq = investor.Equity(account_no="1026090-E")


# In[4]:


#get historical market data
market = investor.MarketData()

#get real time data
realtime = investor.RealtimeDataConnection()


# In[5]:


symbols = ["RJH","VIH","PTTEP","NER","TNP","EKH","VNT","BCH","CHG","RPH","2s","KUN","SPVI","IFS","RAM","AUCT","CGH","BIZ","SNC","RCL"]


# In[6]:


def place_buy_order(symbol,price):
    #get balance
    account_info = eq.get_account_info()
    balance = account_info["data"]["cash_balance"]
    
    #set volume size
    volume = 100
    
    #caculate cost
    cost = price * volume
    
    if cost <= balance:
        #place order
        eq.place_order(symbol=symbol,price_type="LIMIT",price=price,volume=volume,side="buy",pin="000000")
        
        account_info = eq.get_account_info()
        balance = account_info["data"]["cash_balance"]
        print("order made")
        print("symbol: ",symbol)
        print("cost: ",cost)


# In[7]:


def place_sell_order(symbol,price):
    #get porfolio
    portfolio = eq.get_portfolio()
    
    #set volume size
    volume = 100
    
    #check if symbol is in profit
    for x in portfolio:
        if x["symbol"] == symbol:
            if x["percent_profit"] > 100:
                #place order
                eq.place_order(symbol=symbol,price_type="LIMIT",price=price,volume=volume,side="sell",pin="000000")


# In[8]:


def check_signal(symbol):
    #get candle data for each symbol
    candle_data = market.get_candlestick(symbol=symbol,interval="1d")
    
    #create dataframe with candle data
    df = pd.DataFrame()
    df["time"] = pd.to_datetime(candle_data["data"]["time"],unit='s')
    df["open"] = candle_data["data"]["open"]
    df["close"] = candle_data["data"]["close"]
    df["high"] = candle_data["data"]["high"]
    df["low"] = candle_data["data"]["low"]
    df["volume"] = candle_data["data"]["volume"]
    df = df.set_index("time")
    
    #create new columns
    df["middle_band"] = df["close"].rolling(window=20).mean()
    df["upper_band"] = df["middle_band"] + 1.96 * df["close"].rolling(window=20).std()
    df["lower_band"] = df["middle_band"] - 1.96 * df["close"].rolling(window=20).std()
    
    #create signals
    df.loc[df["close"] < (df["middle_band"] * 0.7), "signal"] = "buy"
    df.loc[df["close"] > (df["middle_band"] * 1.2), "signal"] = "sell"
    df.loc[(df["signal"] != "buy") & (df["signal"] != "sell"), "signal"] = "neutral"
    
    #get latest signal and closing price
    last_signal = df.tail().iloc[0]["signal"]
    last_close_price = df.tail().iloc[0]["close"]
    
    #get realtime price for the symbol
    sub = realtime.subscribe_price_info(symbol=symbol,on_message=my_message)
    sub.start()
    
    #handle buy case
    if last_signal == "buy":
        if last_realtime_price <= last_close_price and last_realtime_price != 0.0:
            print(symbol,": buy signal")
            place_buy_order(symbol,last_realtime_price)
    #handle sell case
    elif last_signal == "sell":
        if last_realtime_price >= last_close_price and last_realtime_price != 0.0:
            print(symbol,": sell singal")
    #handle case neutral
    elif last_realtime_price == 0:
        print("market for symbol ", symbol, " is close")
    else:
        print(symbol,": netural")
            
    #stop realtime price subscription
    sub.stop()


# In[9]:


def get_signal_for_stocks(symbols):
    for symbol in symbols:
        check_signal(symbol)


# In[10]:


def my_message(result, subscriber):
    global last_realtime_price
    last_realtime_price = result['data']['last']


# In[11]:


#set global variable
last_realtime_price = 0

#run main function
get_signal_for_stocks(symbols)


# In[ ]:




