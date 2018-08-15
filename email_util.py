import smtplib
from email.mime.text import MIMEText

class Email:
    def __init__(self, subject, body, sender, password, recipient_address):
        self.email = MIMEText(body, 'html')
        self.email['Subject'] = subject
        self.email['From'] = sender
        self.email['To'] = recipient_address

        self.password = password

    def send(self):
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(self.email['From'], self.password)
        server.sendmail(self.email['From'], [self.email['To']], self.email.as_string())
        server.close()

def endline():
    return "<br>"

def bold(string):
    return "<b>" + string + "</b>"

def italics(string):
    return "<i>" + string + "</i>"

def red(string):
    return '<font color="red">' + string + '</font>'

def green(string):
    return '<font color="green">' + string + '</font>'

def money(dollars_as_float):
    amount_str = "$" + "{:,.2f}".format(abs(dollars_as_float))
    return red(amount_str) if dollars_as_float < 0 else green(amount_str)
