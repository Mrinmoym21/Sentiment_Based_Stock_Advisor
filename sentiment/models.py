from django.db import models
from django.contrib.auth.models import User

class StockSentiment(models.Model):
    stock = models.CharField(max_length=20)
    headline = models.TextField()
    sentiment = models.CharField(max_length=10)
    confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)


class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


class UserStock(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    quantity = models.IntegerField()
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stock_symbol} x {self.quantity}"


class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock_symbol = models.CharField(max_length=10)
    action = models.CharField(max_length=4, choices=[('BUY', 'Buy'), ('SELL', 'Sell')])
    quantity = models.PositiveIntegerField()
    price = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} {self.quantity} of {self.stock_symbol}"