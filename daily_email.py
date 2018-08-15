from datetime import datetime, date, timedelta
import pytz
import requests, json
from email_util import Email, endline, bold, italics, money

from config import Configuration
from finance import Finance

# Calendar and email parameters are stored in a JSON file, this loads it
config = Configuration('config.json')

class Event:
    def __init__(self, calendar, title, location, date):
        self.calendar = calendar
        self.title = title
        self.location = location
        self.date = date

    def get_date(self):
        return str(self.date)

class ScheduledEvent(Event):
    def __init__(self, calendar, title, location, startTime, endTime):
        Event.__init__(self, calendar, title, location, startTime.date())
        self.startTime = startTime.astimezone(config.timezone)
        self.endTime = endTime.astimezone(config.timezone)

    # Returns North American-formatted time as string
    def _formattime(self, datetime):
        time_str = str(datetime.strftime('%I:%M %p')) # Format as "HH:MM AM/PM"
        if (time_str[0] == '0'): # Get rid of annoying 0 in "01:30" etc.
            time_str = time_str[1:]
        return time_str

    # Returns event's start time as string
    def get_start(self):
        return self._formattime(self.startTime)

    # Return event's end time as string
    def get_end(self):
        return self._formattime(self.endTime)

class Calendar:
    def __init__(self):
        cronofy_base_url = "https://api.cronofy.com/v1/calendars"
        headers = {"Authorization" : config.cronofy_key}
        r = requests.get(cronofy_base_url, headers=headers)

        self.calendars = {}
        for c in r.json()['calendars']:
            self.calendars[c['calendar_id']] = c['calendar_name']

class Day(Calendar):
    # Lists of the day's events
    all_day_events = []
    schedule_events = []

    # Parse event time if scheduled (i.e. has a time associated)
    def _parsetime(self, time_str):
        return datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
    
    # Instantiates calendar with events from specified date
    def __init__(self, date):
        Calendar.__init__(self)
        end_date = date + timedelta(days=1)

        # Build GET request string
        cronofy_base_url = "https://api.cronofy.com/v1/events?"
        headers = {'Authorization' : config.cronofy_key}
        url = cronofy_base_url + "from=" + date.isoformat() + "&to=" + end_date.isoformat()
        url += "&tzid=America/New_York"
        r = requests.get(url, headers=headers)

        for e in r.json()['events']:
            # Store location, if any
            location = ''
            if 'location' in e:
                location = e['location']['description']
            
            calendar = ''
            if e['calendar_id'] in self.calendars:
                calendar = self.calendars[e['calendar_id']]
            
            # start time format if all-day event: %Y-%m-%d (YYYY-MM-DD, 10 characters)
            # start time format if not all-day: %Y-%m-%dT%H:%M:%SZ
            if len(e['start']) == 10:
                # all-day event
                self.all_day_events.append(Event(calendar, e['summary'], location, date)) # uses the date given to this Day
            else:
                # scheduled event
                start = self._parsetime(e['start'])
                end = self._parsetime(e['end'])
                self.schedule_events.append(ScheduledEvent(calendar, e['summary'], location, start, end))

class Weather():
    def __init__(self, state=config.state, city=config.city):
        url = "http://api.wunderground.com/api/{}/forecast/q/{}/{}.json".format(config.weather_key, state, city)
        r = requests.get(url)

        forecast_day_obj = r.json()['forecast']['txt_forecast']['forecastday']
        self.day_forecast = forecast_day_obj[0]['title'] + ": " + forecast_day_obj[0]['fcttext_metric'] # aw yeah degrees Celcius
        self.night_forecast = forecast_day_obj[1]['title'] + ": " + forecast_day_obj[1]['fcttext_metric']

def main():
    w = Weather()
    d = Day(date.today())

    email_body = "Sup bruh" + endline() + endline()

    email_body += bold("Weather forecast:") + endline()
    email_body += w.day_forecast + endline()
    email_body += w.night_forecast + endline()

    email_body += endline() + bold("Today's calendar has:") + endline()

    for e in d.all_day_events:
        email_body += e.calendar + ", " + italics(e.title) + endline()

    for e in d.schedule_events:
        event_string = e.get_start() + " - " + e.get_end() + ": " + e.calendar + ", " + italics(e.title) + "(" + e.location + ")" + endline()
        email_body += event_string

    f = Finance()

    accts = f.getAccounts()
    acct_changes = {}
    for name in accts.keys():
        acct_changes[name] = 0.0

    transactions = f.getLastNDaysTransactions(1)
    transaction_description = ""
    for t in transactions:
        transaction_description += t.description + ": " + money(t.amount) + ", " + italics(t.account) + endline()
        acct_changes[t.account] += t.amount

    account_desc = ""
    net_worth = 0.0
    for name, val in accts.items():
        account_desc += italics(name) + ": " + money(val)
        net_worth += val
        if (acct_changes[name] != 0.0):
            change = money(acct_changes[name])
            account_desc += ", " + change + " change since yesterday"
        account_desc += endline()

    account_desc += italics("Net worth: ") + money(net_worth) + endline()

    email_body += endline() + bold("Accounts and Transactions") + endline()
    email_body += account_desc + endline() + transaction_description

    print(email_body)
    email = Email("Summary for " + str(date.today()), email_body, config.email_address, 
                  config.email_password, config.recipient_address)
    email.send()

if __name__ == '__main__':
    main()
