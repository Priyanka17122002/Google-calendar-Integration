# Import necessary libraries
import os
import pickle
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Extract Festival Data from HTML

with open("page.html", "r", encoding="utf-8") as f:
    html_content = f.read()

soup = BeautifulSoup(html_content, "html.parser")
festival_data = []
tbody = soup.find("tbody")

for tr in tbody.find_all("tr"):
    tds = tr.find_all("td")
    if len(tds) == 3:
        date = tds[1].get_text(strip=True)
        festival = tds[2].get_text(" ", strip=True)
    elif len(tds) == 2:
        date = tds[0].get_text(strip=True)
        festival = tds[1].get_text(" ", strip=True)
    else:
        continue
    festival_data.append((date, festival))

df = pd.DataFrame(festival_data, columns=["Date", "Festival"])
print("Extracted Festival Data:")
print(df)

# Save extracted data to a CSV file
df.to_csv("festivals_extracted.csv", index=False)


#Convert Dates to ISO Format

def convert_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%d.%m.%y")
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Date conversion error for {date_str}: {e}")
        return None

df["ISO_Date"] = df["Date"].apply(convert_date)
print("DataFrame with ISO Dates:")
print(df)


# Authenticate with Google Calendar

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = "token.pickle"
CLIENT_SECRET_FILE = "client_secret.json"

credentials = None

# Load existing credentials from token.pickle if available
if os.path.exists(TOKEN_PATH):
    with open(TOKEN_PATH, "rb") as token_file:
        credentials = pickle.load(token_file)

# If no valid credentials, authenticate using OAuth
if not credentials or not credentials.valid:
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    credentials = flow.run_local_server(port=8080)  # Change port if needed

    # Save credentials for future use
    with open(TOKEN_PATH, "wb") as token_file:
        pickle.dump(credentials, token_file)

# Build Google Calendar service
service = build("calendar", "v3", credentials=credentials)
calendar_id = "primary"

print("✅ Authentication successful!")




# Fetch existing events from Google Calendar
existing_events = service.events().list(calendarId=calendar_id).execute()
existing_event_dict = {}

# Store existing events in a dictionary (to avoid duplicates)
for event in existing_events.get("items", []):
    event_date = event["start"].get("date")
    event_name = event["summary"].strip()

    # If duplicate event exists, delete it
    if (event_date, event_name) in existing_event_dict:
        print(f"🗑️ Deleting duplicate: {event_name} on {event_date}")
        service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
    else:
        existing_event_dict[(event_date, event_name)] = event["id"]

print("✅ Cleanup completed: Only unique events remain.")

# Insert new festival events into Google Calendar
for _, row in df.iterrows():
    event_date = row["ISO_Date"]
    festival_name = row["Festival"]

    if event_date:
        event = {
            "summary": festival_name,
            "start": {"date": event_date},  # All-day event
            "end": {"date": event_date},
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": 1440},  # 1 day before
                    {"method": "popup", "minutes": 60},    # 1 hour before
                ],
            },
        }

        # ✅ Only add the event if it's not already in the calendar
        if (event_date, festival_name) not in existing_event_dict:
            service.events().insert(calendarId=calendar_id, body=event).execute()
            print(f"🎉 Added event: {festival_name} on {event_date}")
        else:
            print(f"⚠️ Skipping duplicate: {festival_name} on {event_date}")

print("🎯 All festival events have been successfully added to Google Calendar!")
