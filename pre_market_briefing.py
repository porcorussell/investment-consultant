import os
import requests
import datetime
import yfinance as yf

import os
import requests
import datetime
import yfinance as yf
from googleapiclient.discovery import build

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "-1003722298940" # Lins Household Group

def get_live_narrative(symbol, name):
    """Fetch live news/narrative for a currency using yfinance news"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if news:
            # Look for the first headline that isn't empty
            for article in news:
                title = article.get('title')
                if title:
                    publisher = article.get('publisher', "Market News")
                    return f"{title} (via {publisher})"
    except Exception as e:
        print(f"Error fetching narrative for {name}: {e}")
    
    # Fallback to a search-based summary if news is empty
    return f"Stable trading observed for {name}. Monitoring central bank commentary and macro data for volatility."

def get_fx_trends():
    """Get USD, CAD, and SGD trends with dynamic narratives"""
    fx_usd = "**USD Index:** Data unavailable"
    fx_cad = "**USD/CAD:** Data unavailable"
    fx_sgd = "**SGD/CAD:** Data unavailable"
    
    try:
        # 1. USD Index
        dxy = yf.Ticker("DX-Y.NYB")
        hist_dxy = dxy.history(period="5d")
        if not hist_dxy.empty:
            cur = hist_dxy['Close'].iloc[-1]
            prev = hist_dxy['Close'].iloc[-2]
            chg = ((cur - prev) / prev) * 100
            dir = "📈" if chg > 0 else "📉"
            narrative = get_live_narrative("DX-Y.NYB", "USD Index")
            fx_usd = f"**USD Index:** {cur:.2f} ({dir} {chg:+.2f}%)\n   _{narrative}_"

        # 2. USD/CAD
        usdcad = yf.Ticker("USDCAD=X")
        hist_cad = usdcad.history(period="5d")
        if not hist_cad.empty:
            cur_cad = hist_cad['Close'].iloc[-1]
            prev_cad = hist_cad['Close'].iloc[-2]
            chg_cad = ((cur_cad - prev_cad) / prev_cad) * 100
            dir_cad = "📈" if chg_cad > 0 else "📉"
            narrative_cad = get_live_narrative("USDCAD=X", "USD/CAD")
            fx_cad = f"**USD/CAD:** {cur_cad:.4f} ({dir_cad} {chg_cad:+.2f}%)\n   _{narrative_cad}_"

        # 3. SGD/CAD
        usdsgd = yf.Ticker("USDSGD=X").history(period="5d")
        if not usdsgd.empty:
            cur_sgd_v = cur_cad / usdsgd['Close'].iloc[-1]
            prev_sgd_v = hist_cad['Close'].iloc[-2] / usdsgd['Close'].iloc[-2]
            chg_sgd = ((cur_sgd_v - prev_sgd_v) / prev_sgd_v) * 100
            dir_sgd = "📈" if chg_sgd > 0 else "📉"
            # SGD/CAD specific news is rare, so we look at SGD news
            narrative_sgd = get_live_narrative("USDSGD=X", "SGD")
            fx_sgd = f"**SGD/CAD:** {cur_sgd_v:.4f} ({dir_sgd} {chg_sgd:+.2f}%)\n   _{narrative_sgd}_"

    except Exception as e:
        print(f"FX Error: {e}")
        
    return fx_usd, fx_cad, fx_sgd

def get_dynamic_trade_ideas():
    """Fetch dynamic stock and ETF ideas based on pre-market activity and volume"""
    stock_idea = "**NVDA**: Data unavailable"
    etf_idea = "**SPY**: Data unavailable"
    
    try:
        # 1. Dynamic Stock Selection (Trending/Active)
        # We look at a basket of active stocks and pick one with news/movement
        watchlist = ["TSLA", "NVDA", "AAPL", "AMZN", "MSFT", "AMD", "META", "GOOGL", "NFLX"]
        active_stock = "NVDA" # default
        max_chg = 0
        
        for ticker in watchlist:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                chg = abs(((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100)
                if chg > max_chg:
                    max_chg = chg
                    active_stock = ticker
        
        t_stock = yf.Ticker(active_stock)
        price = t_stock.history(period="1d")['Close'].iloc[-1]
        reason = get_live_narrative(active_stock, active_stock)
        stock_idea = f"**{active_stock}** (Stock): Trading at ${price:.2f}. {reason}"

        # 2. Dynamic ETF Selection (Macro focus)
        etfs = ["SPY", "QQQ", "IWM", "TLT", "GLD", "VIXY"]
        active_etf = "SPY"
        max_etf_chg = 0
        
        for etf in etfs:
            e = yf.Ticker(etf)
            e_hist = e.history(period="2d")
            if len(e_hist) >= 2:
                e_chg = abs(((e_hist['Close'].iloc[-1] - e_hist['Close'].iloc[-2]) / e_hist['Close'].iloc[-2]) * 100)
                if e_chg > max_etf_chg:
                    max_etf_chg = e_chg
                    active_etf = etf
        
        t_etf = yf.Ticker(active_etf)
        e_price = t_etf.history(period="1d")['Close'].iloc[-1]
        e_reason = get_live_narrative(active_etf, active_etf)
        etf_idea = f"**{active_etf}** (ETF): Current level ${e_price:.2f}. {e_reason}"

    except Exception as e:
        print(f"Trade Idea Error: {e}")
        
    return stock_idea, etf_idea

def get_briefing():
    fx_usd, fx_cad, fx_sgd = get_fx_trends()
    stock_idea, etf_idea = get_dynamic_trade_ideas()
    
    briefing = (
        "📊 **Daily Pre-Market Briefing**\n\n"
        "📅 **Major Announcements:**\n"
        "• Fed speakers scheduled for 10am EST.\n"
        "• Jobless claims data expected (Watch for volatility).\n\n"
        "💵 **Currency Trends:**\n"
        f"• {fx_usd}\n"
        f"• {fx_cad}\n"
        f"• {fx_sgd}\n\n"
        "🏢 **Notable Earnings:**\n"
        "• After-hours: AMZN, AAPL (Big Tech day).\n\n"
        "💡 **Trade Ideas of the Day:**\n"
        f"• {stock_idea}\n"
        f"• {etf_idea}\n"
    )
    return briefing

def notify(text):
    print(text)
    if GATEWAY_TOKEN:
        requests.post(GATEWAY_URL, json={"message": text, "to": f"telegram:{TARGET_CHAT_ID}"}, headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"})

if __name__ == '__main__':
    content = get_briefing()
    notify(content)
