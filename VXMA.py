import pandas as pd
pd.set_option('display.max_rows', None)
import pandas_ta as ta
import numpy as np
import warnings
warnings.filterwarnings('ignore')
import math 
from ta.trend import adx , macd_diff, sma_indicator
import configparser
config = configparser.ConfigParser()
config.read('config.ini')
#VXMA
#TA setting
ATR_Period = config['TA']['ATR_Period']
ATR_Mutiply = config['TA']['ATR_Mutiply']
RSI_Period = config['TA']['RSI_Period']
EMA_FAST = config['TA']['EMA_Fast']
LINEAR = config['TA']['SUBHAG_LINEAR']
SMOOTH = config['TA']['SMOOTH']
LengthAO = config['TA']['Andean_Oscillator']
ema = int(EMA_FAST)
linear = int(LINEAR)
smooth = int(SMOOTH)
atr_p = int(ATR_Period)
atr_m = float(ATR_Mutiply)
rsi = int(RSI_Period)
AOL = int(LengthAO)

#standard TA weighing
RSI_W = 20
ADX_W = 10
VXMA_W = 40
MACD_W = 20
SMA200_W = 10
bulline = 6
bearline = 4
#Pivot High-Low only calculate last fixed bars
def swinghigh(df,Pivot):
    df['Highest'] = df['High']
    for current in range(len(df.index) - int(Pivot), len(df.index)):
        previous = current - 1
        if df['High'][current] > df['Highest'][previous]:
            df['Highest'][current] = df['High'][current]
        else : df['Highest'][current] = df['Highest'][previous]
    highest = df['Highest'][current]
    return highest

def swinglow(df,Pivot):
    df['Lowest'] = df['Low']
    for current in range(len(df.index) - int(Pivot), len(df.index)):
        previous = current - 1
        if df['Low'][current] < df['Lowest'][previous]:
            df['Lowest'][current] = df['Low'][current]
        else : df['Lowest'][current] = df['Lowest'][previous]
    Lowest = df['Lowest'][current]    
    return Lowest
#Alphatrend

def alphatrend(df,atr_p,atr_m,rsi):
    df['atr'] = ta.sma(ta.true_range(df['High'],df['Low'],df['Close']),atr_p)
    df['rsi'] = ta.rsi(df['Close'],rsi)
    df['adx'] = adx(df['High'],df['Low'],df['Close'])
    df['macd'] = macd_diff(df['Close'])
    df['sma_200'] = sma_indicator(df['Close'],200)
    df['downT'] = 0.0
    df['upT'] = 0.0
    df['alphatrend'] = 0.0
    #AlphaTrend rsibb >= 50 ? upT < nz(AlphaTrend[1]) ? nz(AlphaTrend[1]) : upT : downT > nz(AlphaTrend[1]) ? nz(AlphaTrend[1]) : downT
    for current in range(1, len(df.index)):
        previous = current - 1
        df['downT'][current] = df['High'][current] + df['atr'][current] * atr_m
        df['upT'][current] = df['Low'][current] - df['atr'][current] * atr_m
        if df['rsi'][current] >= 50 :
            if df['upT'][current] < (df['alphatrend'][previous] if df['alphatrend'][previous] != None else 0):
                df['alphatrend'][current] = (df['alphatrend'][previous] if df['alphatrend'][previous] != None else 0)
            else : df['alphatrend'][current] = df['upT'][current]
        else:
            if df['downT'][current] > (df['alphatrend'][previous] if df['alphatrend'][previous] != None else 0):
                df['alphatrend'][current] = (df['alphatrend'][previous] if df['alphatrend'][previous] != None else 0)
            else : df['alphatrend'][current] = df['downT'][current]
    return df
#Andean_Oscillator
def andean(df,AOL):
    df['up1'] = 0.0
    df['up2'] = 0.0
    df['dn1'] = 0.0
    df['dn2'] = 0.0
    df['cmpbull'] = 0.0
    df['cmpbear'] = 0.0
    alpha = 2/(AOL + 1)
    for current in range(1, len(df.index)):
        previous = current - 1
        CloseP = df['Close'][current]
        OpenP = df['Open'][current]
        up1 = df['up1'][previous]
        up2 = df['up2'][previous]
        dn1 = df['dn1'][previous]
        dn2 = df['dn2'][previous]
        # up1 := nz(math.max(C, O, up1[1] - (up1[1] - C) * alpha), C)
        df['up1'][current] = (max(CloseP,OpenP,up1 - (up1 - CloseP)*alpha) if max(CloseP,OpenP,up1 - (up1 - CloseP)*alpha) != None else df['Close'][current])
        # up2 := nz(math.max(C * C, O * O, up2[1] - (up2[1] - C * C) * alpha), C * C)
        df['up2'][current] = (max(CloseP*CloseP,OpenP*OpenP,up2 - (up2 - CloseP*CloseP)*alpha) if max(CloseP*CloseP,OpenP*OpenP,up2 - (up2 - CloseP*CloseP)*alpha) != None else df['Close'][current]*df['Close'][current])
        # dn1 := nz(math.min(C, O, dn1[1] + (C - dn1[1]) * alpha), C)
        df['dn1'][current] = (min(CloseP,OpenP,dn1 + (CloseP - dn1)*alpha) if min(CloseP,OpenP,dn1 + (CloseP - dn1)*alpha) != None else df['Close'][current])
        # dn2 := nz(math.min(C * C, O * O, dn2[1] + (C * C - dn2[1]) * alpha), C * C)
        df['dn2'][current] = (min(CloseP*CloseP,OpenP*OpenP,dn2 + (CloseP*CloseP - dn2)*alpha) if min(CloseP*CloseP,OpenP*OpenP,dn2 + (CloseP*CloseP - dn2)*alpha) != None else df['Close'][current]*df['Close'][current])
        up1n = df['up1'][current] 
        up2n = df['up2'][current]
        dn1n = df['dn1'][current]
        dn2n = df['dn2'][current]
        df['cmpbull'][current] = math.sqrt(dn2n - (dn1n * dn1n))
        df['cmpbear'][current] = math.sqrt(up2n - (up1n * up1n))
    return df
#VXMA Indicator
def vxma(df):
    df['vxma'] = 0.0
    df['trend'] = False
    df['buy'] = False
    df['sell'] = False
    for current in range(2, len(df.index)):
        previous = current - 1
        before  = current - 2
        EMAFAST = df['ema'][current]
        LINREG = df['subhag'][current]
        ALPHATREND = df['alphatrend'][before]
        clohi = max(EMAFAST,LINREG,ALPHATREND)
        clolo = min(EMAFAST,LINREG,ALPHATREND)
            #CloudMA := (bull > bear) ? clolo < nz(CloudMA[1]) ? nz(CloudMA[1]) : clolo :
        if df['cmpbull'][current] > df['cmpbear'][current] :
            if clolo < (df['vxma'][previous] if df['vxma'][previous] != None else 0):
                df['vxma'][current] = (df['vxma'][previous] if df['vxma'][previous] != None else 0)
            else : df['vxma'][current] = clolo
            #  (bear > bull) ? clohi > nz(CloudMA[1]) ? nz(CloudMA[1]) : clohi : nz(CloudMA[1])
        elif df['cmpbull'][current] < df['cmpbear'][current]:
            if clohi > (df['vxma'][previous] if df['vxma'][previous] != None else 0):
                df['vxma'][current] = (df['vxma'][previous] if df['vxma'][previous] != None else 0)
            else : df['vxma'][current] = clohi
        else:
            df['vxma'][current] = (df['vxma'][previous] if df['vxma'][previous] != None else 0)
            #Get trend True = Bull False = Bear
        if df['vxma'][current] > df['vxma'][previous] and df['vxma'][previous] > df['vxma'][before] :
            df['trend'][current] = True
        elif df['vxma'][current] < df['vxma'][previous] and df['vxma'][previous] < df['vxma'][before] :
            df['trend'][current] = False
        else:
            df['trend'][current] = df['trend'][previous] 
            #get zone
        if df['trend'][current] and not df['trend'][previous] :
            df['buy'][current] = True
            df['sell'][current] = False
        elif not df['trend'][current] and df['trend'][previous] :
            df['buy'][current] = False
            df['sell'][current] = True
        else:
            df['buy'][current] = False
            df['sell'][current] = False
    return df

def benchmarking(df):
    df['score'] = 0.0
    for current in range(1, len(df.index)):
        previous = current - 1
        before = current -2
        macd = (10 if float(df['macd'][current]) > 0 else 0)
        adx = (10 if float(df['adx'][current]) > 25 and float(df['adx'][current]) > float(df['adx'][previous])  else 0)
        sma = (10 if float(df['sma_200'][current]) < float(df['Close'][current]) else 0)
        rsi = float(df['rsi'][current])/10
        if df['vxma'][current] > df['vxma'][previous]:
            vxda = 10
        elif df['vxma'][current] < df['vxma'][previous]:
            vxda = 0
        else: vxda = 5
        df['score'][current] = ((macd*MACD_W)/100 + (adx*ADX_W)/100 + (sma*SMA200_W)/100 + (rsi*RSI_W)/100 + (vxda*VXMA_W)/100)
        if df['score'][current] > bulline and df['score'][previous] < bulline and df['score'][before] < bulline:
            df['buy'][current] = True
            df['sell'][current] = False
        elif df['score'][current] < bearline and df['score'][previous] > bearline and df['score'][before] > bearline:
            df['sell'][current] = True
            df['buy'][current] = False
        else : 
            df['buy'][current] = False
            df['sell'][current] = False
    score = float(df['score'][current])
    return score , df


#Build Data Pack for VXMA
def indicator(df):
    df['ema'] = ta.ema(df['Close'],ema)
    df['subhag'] = ta.ema(ta.linreg(df['Close'],linear,0),smooth)
    alphatrend(df,atr_p,atr_m,rsi)
    andean(df,AOL)
    vxma(df)
    score , df =  benchmarking(df)
    return score , df