API_KEY = 'a4f32bf3a03e4bb1a9d17589d4644f38'
import requests
from bs4 import BeautifulSoup


def news_api(stock_name):
    url = (
        f'https://newsapi.org/v2/everything?q={stock_name}&apiKey={API_KEY}&pageSize=5&language=en'
    )
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json().get('articles', [])
        return [article['title'] for article in articles]
    else:
        print(f"News API error: {response.status_code}")
        return []
    
def fetch_news(symbol):
    url = f"https://finviz.com/quote.ashx?t={symbol}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    news_table = soup.find(id='news-table')
    headlines = news_api(symbol)
    if(news_table is None):
        return headlines
    rows = news_table.findAll('tr')
    
    for row in rows:
        headline = row.a.text.strip()
        headlines.append(headline)
    return headlines
