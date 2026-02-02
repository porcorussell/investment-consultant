import os
import requests
import datetime
import yfinance as yf
import feedparser
import re

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "-1003722298940" # Lins Household Group

def get_fundamental_news(query):
    """Search for fundamental drivers (Central Banks, Macro data, Commodities)"""
    # Using news from yfinance as a base, but filtering for macro keywords
    macro_keywords = ["FED", "INFLATION", "CPI", "RATES", "OIL", "CRUDE", "BOC", "MAS", "GDP", "YIELD"]
    narrative = ""
    try:
        ticker = yf.Ticker(query)
        news = ticker.news
        if news:
            for article in news:
                title = article.get('title', "").upper()
                if any(k in title for k in macro_keywords):
                    narrative = f"{article.get('title')} (via {article.get('publisher')})"
                    break
            if not narrative: # fallback to first headline if no macro match
                narrative = f"{news[0].get('title')} (via {news[0].get('publisher')})"
    except:
        pass
    return narrative if narrative else "No specific fundamental catalysts detected in last 24h."

def get_fx_trends():
    """Get USD, CAD, and SGD trends with Fundamental narratives"""
    fx_usd = "**USD Index:** Data unavailable"
    fx_cad = "**USD/CAD:** Data unavailable"
    fx_sgd = "**SGD/CAD:** Data unavailable"
    
    try:
        # 1. USD Index (Macro focus)
        dxy = yf.Ticker("DX-Y.NYB")
        hist_dxy = dxy.history(period="5d")
        if not hist_dxy.empty:
            cur = hist_dxy['Close'].iloc[-1]
            prev = hist_dxy['Close'].iloc[-2]
            chg = ((cur - prev) / prev) * 100
            dir = "📈" if chg > 0 else "📉"
            narrative = get_fundamental_news("DX-Y.NYB")
            fx_usd = f"**USD Index:** {cur:.2f} ({dir} {chg:+.2f}%)\n   _Fundamental Catalyst: {narrative}_"

        # 2. USD/CAD (Oil & Rates focus)
        usdcad = yf.Ticker("USDCAD=X")
        hist_cad = usdcad.history(period="5d")
        if not hist_cad.empty:
            cur_cad = hist_cad['Close'].iloc[-1]
            prev_cad = hist_cad['Close'].iloc[-2]
            chg_cad = ((cur_cad - prev_cad) / prev_cad) * 100
            dir_cad = "📈" if chg_cad > 0 else "📉"
            # Cross reference with Crude Oil for CAD
            oil = yf.Ticker("CL=F").history(period="1d")
            oil_price = oil['Close'].iloc[-1] if not oil.empty else "N/A"
            narrative_cad = get_fundamental_news("USDCAD=X")
            fx_cad = f"**USD/CAD:** {cur_cad:.4f} ({dir_cad} {chg_cad:+.2f}%)\n   _Fundamental Catalyst: {narrative_cad} (Crude Oil: ${oil_price})_"

        # 3. SGD/CAD
        usdsgd = yf.Ticker("USDSGD=X").history(period="5d")
        if not usdsgd.empty:
            cur_sgd_v = cur_cad / usdsgd['Close'].iloc[-1]
            prev_sgd_v = hist_cad['Close'].iloc[-2] / usdsgd['Close'].iloc[-2]
            chg_sgd = ((cur_sgd_v - prev_sgd_v) / prev_sgd_v) * 100
            dir_sgd = "📈" if chg_sgd > 0 else "📉"
            narrative_sgd = get_fundamental_news("USDSGD=X")
            fx_sgd = f"**SGD/CAD:** {cur_sgd_v:.4f} ({dir_sgd} {chg_sgd:+.2f}%)\n   _Fundamental Catalyst: {narrative_sgd}_"
    except:
        pass
        
    return fx_usd, fx_cad, fx_sgd

def get_dynamic_trade_ideas():
    """Research agent focusing on popular financial news."""
    research_section = ""
    feeds = [
        ("MarketWatch", "https://www.marketwatch.com/rss/topstories"),
        ("SeekingAlpha", "https://seekingalpha.com/market_currents.xml"),
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex")
    ]
    
    ideas = []
    keywords = ["UPGRADE", "RALLY", "SINK", "RISE", "FALL", "BREAKOUT", "MOMENTUM"]

    for source_name, url in feeds:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code != 200: continue
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                title_upper = entry.title.upper()
                if any(k in title_upper for k in keywords):
                    snippet = getattr(entry, 'summary', "Details available at source.")
                    snippet = re.sub('<[^<]+?>', '', snippet)[:250]
                    ideas.append({"source": source_name, "title": entry.title, "link": entry.link, "narrative": snippet})
                if len(ideas) >= 3: break
        except: continue
        if len(ideas) >= 3: break

    if ideas:
        for idea in ideas:
            research_section += f"🎯 **{idea['title']}**\n   _Analysis:_ {idea['narrative']}...\n   🔗 [Source ({idea['source']})]({idea['link']})\n\n"
    return research_section

def get_briefing():
    fx_usd, fx_cad, fx_sgd = get_fx_trends()
    research_ideas = get_dynamic_trade_ideas()
    
    briefing = (
        "📊 **Daily Pre-Market Briefing**\n\n"
        "📅 **Major Announcements:**\n"
        "• Fed speakers scheduled for 10am EST.\n"
        "• Jobless claims data expected (Watch for volatility).\n\n"
        "💵 **Currency Trends (Fundamental Focus):**\n"
        f"• {fx_usd}\n"
        f"• {fx_cad}\n"
        f"• {fx_sgd}\n\n"
        "💡 **Research-Driven Trade Ideas:**\n\n"
        f"{research_ideas}"
    )
    return briefing

def notify(text):
    if GATEWAY_TOKEN:
        payload = {"message": text, "to": f"telegram:{TARGET_CHAT_ID}"}
        resp = requests.post(GATEWAY_URL, json=payload, headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"})
        print(f"Notification result: {resp.status_code}")

if __name__ == '__main__':
    content = get_briefing()
    notify(content)
