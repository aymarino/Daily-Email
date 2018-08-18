import iexfinance
from datetime import date

from config import Configuration
from finance import Book
from email_util import Email, endline, bold, money, green, red

config = Configuration('config.json')

def change_money_str(change):
    return ' + ' + money(change) if change > 0 else ' - ' + money(change)

def float_str(change):
    return '{:,.2f}'.format(abs(change))

def pct_change_str(start_value, end_value):
    pct_change = (end_value - start_value) / start_value * 100
    as_pct_str = float_str(pct_change) + '%'
    return green('+' + as_pct_str) if pct_change > 0 else red('-' + as_pct_str)

def get_ticker_summary(book, ticker):
    quantity = book.get_quantity(ticker)
    price_change = book.get_price_change(ticker)
    current_price = book.get_price(ticker)
    prev_price = book.get_price_prev(ticker)

    summary = bold(ticker) + '\t'
    summary += '(' + money(prev_price, color=False) + change_money_str(price_change) + ')'
    summary += ' * ' + "{}".format(quantity)
    summary += ' = ' + money(quantity * prev_price, color=False)
    summary += change_money_str(quantity * price_change)

    pct_change = pct_change_str(prev_price, current_price)
    summary += ' (' + pct_change + ')'

    return summary

def main():
    book = Book('book.json')

    email_body = "Sup" + endline() + endline()
    email_body += bold("Changes in current book:") + endline()

    sorted_positions = sorted(book.book.items(),
                              key = lambda position: book.get_ticker_change(position[0]),
                              reverse = True)

    for ticker in sorted_positions:
        email_body += get_ticker_summary(book, ticker[0]) + endline()
    
    starting_balance = book.get_portfolio_value_prev()
    ending_balance = book.get_portfolio_value()

    email_body += bold("Ending balance") + endline()
    email_body += money(starting_balance)
    email_body += change_money_str(ending_balance - starting_balance)

    pct_change = pct_change_str(starting_balance, ending_balance)
    email_body += ' = ' + money(ending_balance) + ' (' + pct_change + ')'
    
    print(email_body)
    email = Email("Market data for " + str(date.today()), email_body, config.email_address, 
                  config.email_password, config.recipient_address)
    email.send()

if __name__ == '__main__':
    main()
