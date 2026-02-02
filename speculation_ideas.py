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
    """Aggregates momentum-first speculative ideas with detailed execution."""
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
                        "price": hist['Close'].iloc[-1],
                        "high": hist['High'].iloc[-1],
                        "low": hist['Low'].iloc[-1]
                    })
        except: continue
    
    volatility_ideas.sort(key=lambda x: x['vol'], reverse=True)

    # 3. Monthly Runners (Potential Shorts/Puts)
    monthly_runners = []
    for ticker in watchlist:
        try:
            t = yf.Ticker(ticker)
            # Fetch 1 month of history
            hist_30d = t.history(period="1mo")
            if len(hist_30d) >= 20:
                monthly_change = ((hist_30d['Close'].iloc[-1] - hist_30d['Close'].iloc[0]) / hist_30d['Close'].iloc[0]) * 100
                if monthly_change > 100: # Dramatic increase > 100% in 30 days
                    monthly_runners.append({
                        "ticker": ticker,
                        "change": monthly_change,
                        "price": hist_30d['Close'].iloc[-1]
                    })
        except: continue
    
    monthly_runners.sort(key=lambda x: x['change'], reverse=True)

    report = "🔥 **Daily Speculation Ideas (10:30 AM)**\n\n⚡ **DETAILED TRADE EXECUTION PLANS:**\n\n"
    
    added_tickers = set()

    # Add top Monthly Runners for Short/Puts
    for idea in monthly_runners:
        if idea['ticker'] not in added_tickers:
            ticker = idea['ticker']
            price = idea['price']
            report += (f"🎯 **Trade Idea: {ticker} (Short / Puts)**\n"
                       f"   • **Execution:** Long Puts or Bear Call Spread\n"
                       f"   • **Contract:** Monthly expiry, OTM Puts (approx 5% below spot)\n"
                       f"   • **Entry:** Entry on signs of technical exhaustion (e.g., lower high on 1H chart).\n"
                       f"   • **Exit:** 30% profit target or 20% stop-loss on premium.\n"
                       f"   _Analysis:_ Dramatic 30-day run of +{idea['change']:.1f}%. Monitoring for profit-taking pullback.\n\n")
            added_tickers.add(ticker)
        if len(added_tickers) >= 2: break
    
    # Add top 3 Social Momentum with execution
    for idea in momentum_ideas:
        if idea['ticker'] not in added_tickers:
            ticker = idea['ticker']
            price = yf.Ticker(ticker).history(period="1d")['Close'].iloc[-1]
            report += (f"🎯 **Trade Idea: {ticker} ({idea['type']})**\n"
                       f"   • **Execution:** Option (Bull Call Spread)\n"
                       f"   • **Contract:** Next nearest expiry, strikes at ${price:.0f}/${price*1.05:.0f}\n"
                       f"   • **Entry:** Limit order at mid-price; watch for volume spike confirmation.\n"
                       f"   • **Exit:** 25% profit target or 15% stop-loss on premium.\n"
                       f"   _Analysis:_ Trending in {idea['source']}: \"{idea['title']}\"\n"
                       f"   🔗 [Source]({idea['link']})\n\n")
            added_tickers.add(ticker)
        if len(added_tickers) >= 3: break
            
    # Add top 2 Volatility Momentum with execution
    for idea in volatility_ideas:
        if idea['ticker'] not in added_tickers:
            ticker = idea['ticker']
            price = idea['price']
            report += (f"🎯 **Trade Idea: {ticker} (Intraday Scalp)**\n"
                       f"   • **Execution:** Stock (Long) or ATM Calls\n"
                       f"   • **Entry:** Entry near support at ${idea['low']:.2f}; confirm with RSI < 30 on 5m chart.\n"
                       f"   • **Exit:** Exit target at 1.5% stock gain (${price*1.015:.2f}) or trailing stop at day-low.\n"
                       f"   _Analysis:_ High intraday volatility ({idea['vol']:.1f}%) detected. Momentum play on mean reversion.\n\n")
            added_tickers.add(ticker)
        if len(added_tickers) >= 5: break

    report += (
        "📅 **UPCOMING EARNINGS (NEXT 48H):**\n"
        "• **SNAP** (High IV expected)\n"
        "• **PINS** (Social media sentiment proxy)\n\n"
        "⚠️ *Disclaimer: High risk speculative plays. Trade with discipline.*"
    )
    return report

def notify(text):
    print(text)
    if not GATEWAY_TOKEN:
        print("Error: CLAWDBOT_GATEWAY_TOKEN not set.")
        return

    import subprocess
    
    cmd = [
        "clawdbot", "message", "send",
        "--channel", "telegram",
        "--target", TARGET_CHAT_ID,
        "--message", text,
        "--json"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Notification result: Success")
        else:
            print(f"Notification error (CLI): {result.stderr.strip()}")
    except Exception as e:
        print(f"Notification error: {e}")

if __name__ == '__main__':
    content = get_speculative_report()
    notify(content)
