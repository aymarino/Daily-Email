from todoist.api import TodoistAPI
from datetime import datetime
import pytz

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
        local_date = date.astimezone(self.timezone)
        return local_date

    def _parseitem(self, item):
        name = item['content']
        project = self.projects[item['project_id']]
        due_date = self._get_item_due_date(item)
        return Item(name, project, due_date)

    def __init__(self, key, timezone):
        # Sync the items
        self.api = TodoistAPI(key)
        self.api.sync()
        self.timezone = timezone

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

