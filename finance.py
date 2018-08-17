import mintapi
import json
from datetime import datetime, timedelta
import iexfinance

from config import Configuration

# Calendar and email parameters are stored in a JSON file, this loads it
config = Configuration('config.json')

def withinNDays(transactionDate, n):
    return transactionDate.date() >= (datetime.today().date() - timedelta(days=n))

class Transaction:
    def __init__(self, type, amount, account, description):
        self.account = account
        self.description = description
        sign = -1  if type == "debit" else 1
        self.amount = sign * amount

class Finance:
    def __init__(self):
        self.mint = mintapi.Mint(config.mint_email, config.mint_password)

    def getAccounts(self):
        accounts = {}
        for a in self.mint.get_accounts():
            sign = -1 if a['accountType'] == 'credit' else 1
            accounts[a['accountName']] = sign * a['currentBalance']
        return accounts

    def getLastNDaysTransactions(self, days=1):
        allTransactions = self.mint.get_transactions()
        filter = allTransactions.apply(lambda row: withinNDays(row['date'], days), axis=1)

        transactions = []
        for _, t in allTransactions[filter].iterrows():
            transaction = Transaction(t['transaction_type'], t['amount'], t['account_name'], t['description'])
            transactions.append(transaction)

        return transactions

# Caching interface to connect to IEX
class IEXData:
    def __init__(self):
        self.quotes = {}
    
    def get_quote(self, ticker):
        if ticker in self.quotes:
            return self.quotes[ticker]
        else:
            quote = iexfinance.Stock(ticker).get_quote()
            self.quotes[ticker] = quote
            return quote
    
    def get_price(self, ticker):
        return self.get_quote(ticker)['close']
    
    def get_change(self, ticker):
        return self.get_quote(ticker)['change']

class Book:
    def __init__(self, data_source):
        with open(data_source) as book_json_file:
            self.book = json.load(book_json_file)
            self.iex_interface = IEXData()
    
    def get_quantity(self, ticker):
        return self.book[ticker]
    
    def get_price(self, ticker):
        return self.iex_interface.get_price(ticker)

    # 'Previous' value being teh point-of-reference from the quote
    # I.e. previous day's close
    def get_price_prev(self, ticker):
        return self.get_price(ticker) - self.get_ticker_change(ticker)
    
    def get_value(self, ticker):
        return self.get_quantity(ticker) * self.get_price(ticker)
    
    def get_ticker_change(self, ticker):
        return self.iex_interface.get_change(ticker)

    def get_portfolio_value(self):
        return sum([self.get_value(ticker) for ticker in self.book])

    # 'Previous' value being the point-of-reference from the quote.
    # I.e. previous day's close.
    def get_portfolio_value_prev(self):
        return sum([self.get_price_prev(ticker) * self.get_quantity(ticker)
                    for ticker in self.book])
    