import os
import json
import datetime
import yfinance as yf
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .models import Portfolio, UserStock, Trade, StockSentiment
from .sentiment_backtest import fetch_news_for_date, analyze_sentiments, simulate_trade
from .news_scraper import fetch_news

def home(request):
    json_path = os.path.join(settings.BASE_DIR,'sentiment', 'static', 'stocks.json')
    with open(json_path, 'r') as f:
        stocks = json.load(f)
    return render(request, 'home.html', {'stocks': stocks})

def get_stock_symbols(request):
    json_path = os.path.join(settings.BASE_DIR,'sentiment', 'static', 'stocks.json')
    with open(json_path, 'r') as f:
        stocks = json.load(f)
    return render(request, 'stocks_symbol.html', {'stocks': stocks})

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email    = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        login(request, user)
        return redirect('dashboard')

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

def contact_us(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        messages.success(request, "Your message has been sent successfully.")
        return redirect('home')
    
    return render(request, 'contact_us.html')

@login_required
def dashboard_view(request):
    portfolio, _ = Portfolio.objects.get_or_create(user=request.user)
    stocks = UserStock.objects.filter(portfolio=portfolio)

    return render(request, 'dashboard.html',{
        'stocks': stocks
    })

@login_required
def add_stock(request):
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        quantity = int(request.POST.get('quantity'))
        portfolio, created = Portfolio.objects.get_or_create(user=request.user)
        existing_stock = UserStock.objects.filter(portfolio=portfolio, stock_symbol=symbol.upper()).first()
        if existing_stock:
            existing_stock.quantity += quantity
            existing_stock.save()
            message = f'Updated quantity: Now you have {existing_stock.quantity} shares of {symbol.upper()}'
        else:
            UserStock.objects.create(portfolio=portfolio, stock_symbol=symbol.upper(), quantity=quantity)
            message = f'Added {quantity} shares of {symbol.upper()} to your portfolio'
        
        return JsonResponse({'message': message})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def remove_stock(request):
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        quantity = int(request.POST.get('quantity', 0))  

        if quantity <= 0:
            return JsonResponse({'error': 'Invalid quantity'}, status=400)

        portfolio = get_object_or_404(Portfolio, user=request.user)
        stock = UserStock.objects.filter(portfolio=portfolio, stock_symbol=symbol.upper()).first()

        if stock:
            if stock.quantity > quantity:
                stock.quantity -= quantity
                stock.save()
                return JsonResponse({'message': f'Removed {quantity} shares of {symbol.upper()}. Remaining: {stock.quantity}'})
            elif stock.quantity == quantity:
                stock.delete()
                return JsonResponse({'message': f'Removed all {quantity} shares of {symbol.upper()}'})
            else:
                return JsonResponse({'error': f'Cannot remove {quantity} shares. You only have {stock.quantity} shares.'}, status=400)
        
        return JsonResponse({'error': 'Stock not found in portfolio'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def portfolio_valuation(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    stocks = UserStock.objects.filter(portfolio=portfolio)

    valuation = []
    total = 0.0

    for stock in stocks:
        data = yf.Ticker(stock.stock_symbol).history(period="1d")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            value = current_price * stock.quantity
            total += value
            valuation.append({
                'symbol': stock.stock_symbol,
                'quantity': stock.quantity,
                'price': round(current_price, 2),
                'value': round(value, 2)
            })

    return JsonResponse({'total_value': round(total, 2), 'stocks': valuation})

@login_required
def sentiment_view(request):
    if request.method == 'POST':
        stock = request.POST.get('stock_query').upper()
        news_list = fetch_news(stock)
        sentiments = analyze_sentiments(news_list)
        data = []
        score_sum = 0
        count = 0
        for item in sentiments:
            score_sum += round(item['score'], 4)
            count += 1

        avg_score = score_sum / count if count > 0 else 0
        if avg_score > 0.3:
            decision = "Buy"
        elif avg_score < -0.3:
            decision = "Sell"
        else:
            decision = "Hold"

        for entry in sentiments:
            StockSentiment.objects.create(
                stock=stock,
                headline=entry['headline'],
                sentiment=entry['sentiment'],
                confidence=entry['score']
            )
            data.append(entry)

        return render(request, 'sentiment.html', {"sentiments":data, "decision": decision, "avg_score":avg_score})
    return render(request, 'sentiment.html')



@login_required
def simulate_trade_view(request):
    if request.method == 'POST':
        stock = request.POST['symbol'].upper()
        action = request.POST['action']
        quantity = int(request.POST['quantity'])

        total, price = simulate_trade(stock, action, quantity)
        Trade.objects.create(
            user=request.user,
            stock_symbol=stock,
            action=action,
            quantity=quantity,
            price=price
        )
        return render(request, 'simulate_trade.html',{'success': True, 'total': total, 'price': price, 'symbol': stock})
    return render(request, 'simulate_trade.html')



@login_required
def backtest_view(request):
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        start_date = request.POST.get('start_date', '2025-01-01')
        end_date = request.POST.get('end_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        
        price_data = yf.download(symbol, start_date, end_date)
        price_data.index = price_data.index.strftime('%Y-%m-%d')
    
        sentiment_scores = []
        headlines_list = []
        list_price=price_data[('Close', symbol)].tolist()
        list_index=price_data.index.tolist()
        for date in list_index:
            headlines = fetch_news_for_date(symbol, date)
            headlines_list.append(headlines)
            if headlines:
                sentiment_results = analyze_sentiments(headlines)
                avg_score = sum([r['score'] for r in sentiment_results]) / len(sentiment_results)
                sentiment_scores.append(round(avg_score, 4))
            else:
                sentiment_scores.append(0.0)
                
        signals = []
        for score in sentiment_scores:
            if score > 0.3:
                signals.append('buy')
            elif score < -0.3:
                signals.append('sell')
            else:
                signals.append('hold')
        
        # Prepare data for template
        
        result = {
            'symbol': symbol.upper(),
            'dates': list_index,
            'prices': list_price,
            'sentiments': sentiment_scores,
            'signals': signals,
            'headlines': headlines_list,
            'start_date': start_date,
            'end_date': end_date,
            'combined_data': list(zip(list_index, 
                                    list_price, 
                                    sentiment_scores, 
                                    signals,
                                    headlines_list))
        }
        result['chart_data'] = json.dumps({
                            'dates': list_index,
                            'prices': list_price,
                            'sentiments': sentiment_scores
                        })
        total_signals = len([s for s in signals if s in ['buy', 'sell']])
        buy_signals = signals.count('buy')
        sell_signals = signals.count('sell')
        hold_signals = signals.count('hold')

        result['metrics'] = {
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'total_signals': total_signals
        }
        
        return render(request, 'backtest.html', {'result': result})
    
    return render(request, 'backtest.html')