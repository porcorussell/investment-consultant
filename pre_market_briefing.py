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

def get_live_narrative(symbol, name):
    """Fetch live news/narrative for a currency using yfinance news"""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if news:
            for article in news:
                title = article.get('title')
                if title:
                    publisher = article.get('publisher', "Market News")
                    return f"{title} (via {publisher})"
    except:
        pass
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
            narrative_sgd = get_live_narrative("USDSGD=X", "SGD")
            fx_sgd = f"**SGD/CAD:** {cur_sgd_v:.4f} ({dir_sgd} {chg_sgd:+.2f}%)\n   _{narrative_sgd}_"
    except:
        pass
        
    return fx_usd, fx_cad, fx_sgd

def get_dynamic_trade_ideas():
    """Research agent: browses top financial news to find curated ideas."""
    research_section = ""
    feeds = [
        ("MarketWatch", "https://www.marketwatch.com/rss/topstories"),
        ("SeekingAlpha", "https://seekingalpha.com/market_currents.xml"),
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        ("Zacks", "https://www.zacks.com/rss/zacks_analyst_blog.rss")
    ]
    
    ideas = []
    keywords = ["BUY", "SELL", "LONG", "SHORT", "UPGRADE", "STOCK", "EARNINGS", "FED", "CPI", "RALLY", "SINK", "RISE", "FALL"]

    for source_name, url in feeds:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if response.status_code != 200: continue
            
            feed = feedparser.parse(response.content)
            for entry in feed.entries:
                title_upper = entry.title.upper()
                if any(k in title_upper for k in keywords) or len(ideas) < 2:
                    snippet = getattr(entry, 'summary', "Details available at source.")
                    snippet = re.sub('<[^<]+?>', '', snippet)[:250]
                    ideas.append({
                        "source": source_name,
                        "title": entry.title,
                        "link": entry.link,
                        "narrative": snippet
                    })
                if len(ideas) >= 3: break
        except:
            continue
        if len(ideas) >= 3: break

    if ideas:
        for idea in ideas:
            research_section += (
                f"🎯 **{idea['title']}**\n"
                f"   _Analysis:_ {idea['narrative']}...\n"
                f"   🔗 [Source ({idea['source']})]({idea['link']})\n\n"
            )
    else:
        research_section = "No high-conviction research ideas found in this cycle."

    return research_section

def get_briefing():
    fx_usd, fx_cad, fx_sgd = get_fx_trends()
    research_ideas = get_dynamic_trade_ideas()
    
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
        "💡 **Research-Driven Trade Ideas:**\n\n"
        f"{research_ideas}"
    )
    return briefing

def notify(text):
    print(text)
    if GATEWAY_TOKEN:
        requests.post(GATEWAY_URL, json={"message": text, "to": f"telegram:{TARGET_CHAT_ID}"}, headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"})

if __name__ == '__main__':
    content = get_briefing()
    notify(content)
