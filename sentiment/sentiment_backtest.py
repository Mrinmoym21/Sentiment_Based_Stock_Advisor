import yfinance as yf
from datetime import datetime, timedelta, date
from typing import List
import requests
from bs4 import BeautifulSoup
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer

MODEL_NAME = "yiyanghkust/finbert-tone"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

# Create sentiment analysis pipeline
sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
    device=-1
)

def analyze_sentiments(headlines):
    results = sentiment_pipeline(headlines)
    output = []
    for i, result in enumerate(results):
        score = result['score']
        if result['label'] == 'Positive':
            final_score = score
        elif result['label'] == 'Negative':
            final_score = -score
        else:  # neutral
            final_score = 0.0

        output.append({
            'headline': headlines[i],
            'sentiment': result['label'].upper(),  # to match 'POSITIVE' / 'NEGATIVE'
            'score': round(final_score, 4)
        })
    return output




API_KEY="3c6b27ca24d5461e83f9b784950af8da"
#API_KEY = 'a4f32bf3a03e4bb1a9d17589d4644f38'
def fetch_news_for_date(symbol: str, target_date: str) -> List[str]:
    date_obj = datetime.strptime(target_date, "%Y-%m-%d")
    next_date = date_obj + timedelta(days=1)
    url = (
         f'https://newsapi.org/v2/everything?q={symbol}&from={target_date}&to={next_date}&sortBy=popularity&apiKey={API_KEY}'
    )
    response = requests.get(url)
    headlines = []
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        headlines.extend( [article['title'] for article in articles])
    
    # # Fetch from FinViz
    
    url = f"https://finviz.com/quote.ashx?t={symbol}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    news_table = soup.find(id='news-table')
    
    if news_table:
        rows = news_table.find_all('tr')
        for row in rows:
            td = row.find_all('td')
            if len(td) > 1:
                time_or_date = td[0].text.strip().split(' ')[0]

            if '-' in time_or_date:
                try:
                    current_date = datetime.strptime(time_or_date, '%b-%d-%y').strftime('%Y-%m-%d')
                except ValueError:
                    continue
            elif time_or_date == "Today":
                current_date = date.today().strftime('%Y-%m-%d')
            elif time_or_date == "Yesterday":
                current_date = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

            if current_date == target_date:
                headline = td[1].a.text.strip()
                headlines.append(headline)
    
    return headlines

def get_daily_sentiment(symbol: str, date: str) -> float:
    """Get average sentiment score for a specific day"""
    headlines = fetch_news_for_date(symbol, date)
    if not headlines:
        return 0.0  # Neutral if no news
    
    sentiment_results = analyze_sentiments(headlines)
    avg_score = sum([r['score'] for r in sentiment_results]) / len(sentiment_results)
    return avg_score

def simulate_trade(stock, action, quantity):
    ticker = yf.Ticker(stock)
    data = ticker.history(period="1d")
    if not data.empty:
        price = data['Close'].iloc[-1]
        return round(price * quantity, 2), round(price, 2)
    return 0, 0


    
    
    