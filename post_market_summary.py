import os
import requests
import datetime
import yfinance as yf

# Configuration
GATEWAY_URL = "http://127.0.0.1:18789/v1/message"
GATEWAY_TOKEN = os.getenv("CLAWDBOT_GATEWAY_TOKEN")
TARGET_CHAT_ID = "-1003722298940" # Lins Household Group

def get_market_summary():
    """Fetch stocks with surprising movements and market summary"""
    # Fetch a broader set of active tickers and filter for highest volatility
    potential_tickers = ["AAPL", "AMZN", "MSFT", "GOOGL", "TSLA", "NVDA", "META", "NFLX", "AMD", "INTC", "SMCI", "COIN"]
    
    movers = []
    for ticker in potential_tickers:
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="1d")
            info = t.info
            
            if not hist.empty:
                close_price = hist['Close'].iloc[-1]
                prev_close = info.get('previousClose', close_price)
                change = ((close_price - prev_close) / prev_close) * 100
                
                movers.append({
                    'ticker': ticker,
                    'price': close_price,
                    'change': change,
                    'high_52': info.get('fiftyTwoWeekHigh', 0),
                    'target_low': info.get('targetLowPrice', 0),
                    'target_high': info.get('targetHighPrice', 0)
                })
        except:
            continue

    # Sort by absolute change to find "surprising" or big movements
    movers.sort(key=lambda x: abs(x['change']), reverse=True)
    top_movers = movers[:5] # Top 5 biggest movers

    summary_lines = []
    for m in top_movers:
        # Fetch news summary for the ticker
        reason = "Market sentiment shift."
        try:
            news = t.news
            if news:
                # Get the first news title as a proxy for the reason
                reason = news[0].get('title', "Volatility in trading.")
        except:
            pass

        emoji = "🚀" if m['change'] > 0 else "🩸"
        line = (f"• **{m['ticker']}:** ${m['price']:.2f} ({emoji} {m['change']:+.2f}%) | "
                f"52w High: ${m['high_52']:.2f} | "
                f"Analysts: ${m['target_low']:.2f} - ${m['target_high']:.2f}\n"
                f"   _Reason: {reason}_")
        summary_lines.append(line)

    # Major events narrative (Placeholder for now, can be enriched with News API)
    events_narrative = (
        "• Markets reacted to Big Tech earnings results and Fed commentary.\n"
        "• Volatility increased in afternoon trading following labor data releases."
    )

    report = (
        "🔔 **Post-Market Summary**\n\n"
        "📈 **Key Market Events:**\n"
        f"{events_narrative}\n\n"
        "🏢 **Notable Stock Performance & Analyst Targets:**\n"
        + "\n".join(summary_lines)
    )
    return report

def notify(text):
    print(text)
    if GATEWAY_TOKEN:
        requests.post(GATEWAY_URL, json={"message": text, "to": f"telegram:{TARGET_CHAT_ID}"}, headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"})

if __name__ == '__main__':
    content = get_market_summary()
    notify(content)
