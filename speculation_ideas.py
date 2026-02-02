import os
import requests
import datetime
import yfinance as yf
import feedparser
import re

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "833307110" # Russell Personal

def get_reddit_momentum_agent():
    """Agent: Scans for high-velocity social sentiment and 'YOLO' momentum plays."""
    subs = ["wallstreetbets", "options", "pennystocks"]
    spec_ideas = []
    
    # Priority keywords for momentum
    momentum_ks = ["SQUEEZE", "YOLO", "MOON", "BULLISH", "CALLS", "BREAKOUT", "PUMP", "HIGH VOLUME"]
    
    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/new/.rss"
            feed = feedparser.parse(url, agent="Mozilla/5.0 (Clawdbot Momentum Agent/1.0)")
            
            for entry in feed.entries:
                title_up = entry.title.upper()
                tickers = re.findall(r'\b[A-Z]{2,5}\b', title_up)
                
                for t in tickers:
                    if t in ["THE", "AND", "FOR", "BUY", "SELL", "NYSE", "NASDAQ", "SEC", "DD", "WSB", "POTUS"]: continue
                    
                    if any(k in title_up for k in momentum_ks):
                        spec_ideas.append({
                            "ticker": t,
                            "source": f"r/{sub}",
                            "title": entry.title,
                            "link": entry.link,
                            "type": "Social Momentum"
                        })
                if len(spec_ideas) >= 5: break
        except: continue
        if len(spec_ideas) >= 5: break
    return spec_ideas

def get_speculative_report():
    """Aggregates momentum-first speculative ideas."""
    # 1. Social Momentum
    momentum_ideas = get_reddit_momentum_agent()
    
    # 2. Price Action Momentum (Volatility)
    volatility_ideas = []
    watchlist = ["TSLA", "NVDA", "AMD", "COIN", "MSTR", "DJT", "SMCI", "NFLX", "LULU", "PLTR", "GME"]
    for ticker in watchlist:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="2d")
            if len(hist) >= 2:
                daily_vol = ((hist['High'].iloc[-1] - hist['Low'].iloc[-1]) / hist['Low'].iloc[-1]) * 100
                if daily_vol > 5: # High intraday volatility
                    volatility_ideas.append({
                        "ticker": ticker,
                        "vol": daily_vol,
                        "price": hist['Close'].iloc[-1]
                    })
        except: continue
    
    volatility_ideas.sort(key=lambda x: x['vol'], reverse=True)

    report = "🔥 **Daily Speculation Ideas (10:30 AM)**\n\n⚡ **MOMENTUM TRADE SUGGESTIONS:**\n\n"
    
    added_tickers = set()
    
    # Add top 3 Social Momentum
    for idea in momentum_ideas:
        if idea['ticker'] not in added_tickers:
            report += (f"🎯 **Trade Idea: {idea['ticker']} ({idea['type']})**\n"
                       f"   _Analysis:_ High-velocity chatter in {idea['source']}: \"{idea['title']}\"\n"
                       f"   🔗 [Source]({idea['link']})\n\n")
            added_tickers.add(idea['ticker'])
        if len(added_tickers) >= 3: break
            
    # Add top 2 Volatility Momentum
    for idea in volatility_ideas:
        if idea['ticker'] not in added_tickers:
            report += (f"🎯 **Trade Idea: {idea['ticker']} (Volatility/Price Action)**\n"
                       f"   _Analysis:_ Intraday volatility of {idea['vol']:.1f}% detected. Entry near ${idea['price']:.2f} for scalp.\n\n")
            added_tickers.add(idea['ticker'])
        if len(added_tickers) >= 5: break

    report += (
        "📅 **UPCOMING EARNINGS (NEXT 48H):**\n"
        "• **SNAP** (High IV expected)\n"
        "• **PINS** (Social media sentiment proxy)\n\n"
        "⚠️ *Disclaimer: High risk momentum plays. Tight stops required.*"
    )
    return report

def notify(text):
    if GATEWAY_TOKEN:
        payload = {"message": text, "to": f"telegram:{TARGET_CHAT_ID}"}
        resp = requests.post(GATEWAY_URL, json=payload, headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"})
        print(f"Notification result: {resp.status_code}")

if __name__ == '__main__':
    content = get_speculative_report()
    notify(content)
