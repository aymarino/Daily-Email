from datetime import datetime, date, timedelta
import pytz

import requests, json

import smtplib
from email.mime.text import MIMEText

from todoist.api import TodoistAPI

# Calendar and email parameters are stored in a JSON file, this loads it
class Configuration:
    def __init__(self, filename):
        with open(filename) as config_file:
            config = json.load(config_file)

            self.cronofy_key = config['cronofy_key']
            self.todoist_key = config['todoist_key']
            self.timezone = pytz.timezone(config['timezone'])
            self.email_address = config['email_address']
            self.email_password = config['email_password']
            self.recipient_address = config['recipient_address']
            self.weather_key = config['wunderground_key']
            self.state = config['state']
            self.city = config['city']

config = Configuration('config.json')

class Email:
    def __init__(self, subject, body,
        sender=config.email_address,
        password=config.email_password,
        recipient_address=config.recipient_address):

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

class Item:
    def __init__(self, name, project, due):
        self.name = name
        self.project = project
        self.due_date = due
    
    def get_date(self):
        return self.due_date.strftime('%a, %b %d')

class Todo:
    def _get_item_due_date(self, item):
        time_str = item['due_date_utc'][:-6]
        date = datetime.strptime(time_str, '%a %d %b %Y %H:%M:%S').replace(tzinfo=pytz.UTC) 
        local_date = date.astimezone(config.timezone)
        return local_date

    def _parseitem(self, item):
        name = item['content']
        project = self.projects[item['project_id']]
        due_date = self._get_item_due_date(item)
        return Item(name, project, due_date)

    def __init__(self):
        # Sync the items
        self.api = TodoistAPI(config.todoist_key)
        self.api.sync()

        # Associate project id with names
        self.projects = {}
        for project in self.api.state['projects']:
            self.projects[project['id']] = project['name']
    
    def get_due_items(self):
        due_items = []
        today = datetime.utcnow()
        for item in self.api.state['items']:
            if item['checked'] == 1:
                continue
            due_date = item['due_date_utc']
            if (due_date):
                due_utc = datetime.strptime(due_date[:15], '%a %d %b %Y')
                if due_utc < today:
                    due_items.append(self._parseitem(item))
        # Sort items by due date
        due_items.sort(key=lambda item: item.due_date)
        return due_items

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

def endline():
    return "<br>"

def header(string):
    return "<b>" + string + "</b>"

def main():
    w = Weather()
    d = Day(date.today())

    email_body = "Sup bruh" + endline() + endline()

    email_body += header("Weather forecast:") + endline()
    email_body += w.day_forecast + endline()
    email_body += w.night_forecast + endline()

    email_body += endline() + header("Today's calendar has:") + endline()

    for e in d.all_day_events:
        email_body += e.calendar + ", <i>" + e.title + "</i>" + endline()

    for e in d.schedule_events:
        event_string = e.get_start() + " - " + e.get_end() + ": " + e.calendar + ", <i>" + e.title + "</i> (" + e.location + ")" + endline()
        email_body += event_string

    email_body += endline() + header("Todo list for today:") + endline()

    t = Todo()
    due = t.get_due_items()
    for item in due:
        item_str = item.get_date() + ": " + item.name + ", "
        item_str += "<i>" + item.project + "</i>" + endline()
        email_body += item_str

    print(email_body)
    email = Email("Summary for " + str(date.today()), email_body)
    email.send()

if __name__ == '__main__':
    main()
