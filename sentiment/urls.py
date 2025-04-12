from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    # path('analyze/<str:stock>/', views.analyze_sentiment),
    path('sentiment/', views.sentiment_view, name='sentiment'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('portfolio/add/', views.add_stock, name='add_stock'),
    path('portfolio/remove/', views.remove_stock, name='remove_stock'),
    path('portfolio/value/', views.portfolio_valuation, name='portfolio_value'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('simulate-trade/', views.simulate_trade_view, name='simulate_trade'),
    path('backtest/', views.backtest_view, name='backtest'),
    path('stocks-symbols/', views.get_stock_symbols, name='get_stock_symbols'),
]
