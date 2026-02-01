import os
import requests
import datetime
import yfinance as yf
from googleapiclient.discovery import build

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "-1003722298940" # Lins Household Group

def get_fx_trends():
    """Get USD and CAD trends with short narrative"""
    try:
        # USD Index (approx via DX-Y.NYB)
        dxy = yf.Ticker("DX-Y.NYB")
        hist_dxy = dxy.history(period="5d")
        if not hist_dxy.empty:
            current = hist_dxy['Close'].iloc[-1]
            prev = hist_dxy['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            dxy_dir = "📈" if change > 0 else "📉"
            
            # Simple narrative logic
            if change > 0.1:
                usd_narrative = "USD is showing strength as yields remain elevated; outlook remains bullish."
            elif change < -0.1:
                usd_narrative = "USD is softening on cooling inflation data; testing support levels."
            else:
                usd_narrative = "USD is trading sideways; market waiting for next macro catalyst."
                
            fx_usd = f"**USD Index:** {current:.2f} ({dxy_dir} {change:+.2f}%)\n   _{usd_narrative}_"
        else:
            fx_usd = "**USD Index:** Data unavailable"

        # USD/CAD
        usdcad = yf.Ticker("CAD=X")
        hist_cad = usdcad.history(period="5d")
        if len(hist_cad) >= 2:
            current = hist_cad['Close'].iloc[-1]
            prev = hist_cad['Close'].iloc[-2]
            change = ((current - prev) / prev) * 100
            cad_dir = "📈" if change > 0 else "📉"
            
            # Simple narrative logic
            if current > 1.41:
                cad_narrative = "CAD under pressure from weak crude prices; 1.42 level in sight."
            elif current < 1.39:
                cad_narrative = "Loonie strengthening on positive domestic growth sentiment."
            else:
                cad_narrative = "CAD hovering in neutral range; tracking closely with commodities."
                
            fx_cad = f"**USD/CAD:** {current:.4f} ({cad_dir} {change:+.2f}%)\n   _{cad_narrative}_"
        else:
            fx_cad = "**USD/CAD:** Data unavailable"
            
        return fx_usd, fx_cad
    except:
        return "**USD:** N/A", "**CAD:** N/A"

def get_briefing():
    fx_usd, fx_cad = get_fx_trends()
    
    # Trade Ideas (1 Stock, 1 ETF)
    try:
        # Stock Idea
        stock_ticker = "NVDA"
        t_stock = yf.Ticker(stock_ticker)
        stock_price = t_stock.history(period="1d")['Close'].iloc[-1]
        stock_idea = f"**{stock_ticker}** (Stock - Long): AI infrastructure demand remains the primary driver. Entry near ${stock_price:.2f}."
        
        # ETF Idea
        etf_ticker = "SPY"
        t_etf = yf.Ticker(etf_ticker)
        etf_price = t_etf.history(period="1d")['Close'].iloc[-1]
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
        f"• {fx_cad}\n\n"
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
