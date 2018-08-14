import mintapi
import json
from datetime import datetime, timedelta

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
        for idx, t in allTransactions[filter].iterrows():
            transaction = Transaction(t['transaction_type'], t['amount'], t['account_name'], t['description'])
            transactions.append(transaction)

        return transactions
