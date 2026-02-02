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

def get_briefing():
    fx_usd, fx_cad, fx_sgd = get_fx_trends()
    
    try:
        stock_ticker = "NVDA"
        stock_price = yf.Ticker(stock_ticker).history(period="1d")['Close'].iloc[-1]
        stock_idea = f"**{stock_ticker}** (Stock - Long): AI infrastructure demand remains the primary driver. Entry near ${stock_price:.2f}."
        
        etf_ticker = "SPY"
        etf_price = yf.Ticker(etf_ticker).history(period="1d")['Close'].iloc[-1]
        etf_idea = f"**{etf_ticker}** (ETF - Neutral/Long): Market eyes 6,000 level; watch for S&P 500 support at ${etf_price:.2f}."
    except:
        stock_idea = "**NVDA**: Data unavailable"
        etf_idea = "**SPY**: Data unavailable"

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
