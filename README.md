# Daily Email Summary

## Motivation

I'm usually a pretty organized person; I put tasks, events, appointments, etc. in my calendar and *usually* don't have any problem keeping those appointments.
But recently I missed an appointment out of the blue, mainly because even though they'll all in my calendar, I don't actually remember to check it and don't really plan accordingly until I get that 10-minute alert way too late to actually do anything about it.

My solution is to take the "remember" part out of checking my calendar and emailing the day's schedule and events to myself every morning.
Ideally, this will force me to plan ahead if there are any one-off appointments I need to make but need to plan in advance for.

## Features

* Daily weather forecast, because why not?
* Pulls your Google Calendar via the Cronofy API (Google's OAuth2 version of the API would require me to sign in every day to renew the auth token).
Displays all-day and scheduled events separately.

### Feature ideas

* Financial display: status of bank and investment accounts (and +/- change since yesterday)
* Todoist integration: tasks due today (and overdue)

## Usage

When you run the `daily_email.py` script, it reads certain parameters from a config JSON file (in the current script, called simply `config.json`).
The current format of the JSON configuration file is as follows:

```json
{
  "cronofy_key": "Bearer xxxxxxxxxxxxxxx",
  "timezone" : "US/Eastern",
  "email_address" : "<sender email address>",
  "email_password" : "<sender email password>",
  "recipient_address" : "<recipient email address>",
  "wunderground_key" : "xxxxxxxxxxxxxxxx",
  "state" : "MI",
  "city" : "Ann_Arbor"
}

```

and sends an email in the following format (today's as an example):

```
Sup bruh

Weather forecast:
Monday: Cloudy with snow. High -3C. Winds E at 15 to 25 km/h. Chance of snow 80%. 3-7cm of snow expected.
Monday Night: Intermittent snow showers, especially early. Low -8C. Winds NE at 15 to 30 km/h. Chance of snow 40%.

Today's calendar has:
1:30 PM - 3:00 PM: EECS 483 Lecture (1311 EECS)
5:00 PM - 7:00 PM: EECS 281 Lab (TA) (185 EWRE)
```

### Setting up for automatic emailing

To get the desired "automatic" mail every morning at a certain time, I set a cron job running on an Amazon EC2 Linux VM.
Since the VM is set to UTC, this was the necessary set up to get the email at 7:30 AM eastern time:

```
30 11 * * * python ~/Daily-Email/daily_email.py
```

