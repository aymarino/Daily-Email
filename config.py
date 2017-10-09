import json
import pytz

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
            self.mint_email = config['mint_email']
            self.mint_password = config['mint_password']
            self.mint_ius_session = config['mint_ius_session']
            self.mint_thx_guid = config['mint_thx_guid']
