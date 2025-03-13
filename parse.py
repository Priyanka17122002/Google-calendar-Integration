import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the website
url = "https://heb.org.sg/majorfestivals/"

# Set headers to mimic a browser
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/",  # Helps bypass some restrictions
    "Accept-Language": "en-US,en;q=0.9"
}


# Send a GET request
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find the festival table
    table = soup.find("table")  # Locate the first table in the page
    
    if table:
        # Extract table rows
        rows = table.find_all("tr")
        
        # Store data
        festival_data = []

        # Loop through rows (skip header row)
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 2:  # Ensure valid columns exist
                festival = cols[0].text.strip()  # Festival Name
                date = cols[1].text.strip()  # Date
                festival_data.append([festival, date])

        # Convert to Pandas DataFrame
        df = pd.DataFrame(festival_data, columns=["Festival", "Date"])
        
        # Print the table
        print(df)
    else:
        print("Table not found on the page.")
else:
    print(f"Failed to retrieve the webpage. Status Code: {response.status_code}")
