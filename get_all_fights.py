import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

EVENTS_URL = "http://ufcstats.com/statistics/events/completed?page="

def get_page_html(page_number):
    url = EVENTS_URL + str(page_number)
    response = requests.get(url)
    return BeautifulSoup(response.content, "html.parser")

page_number = 1
all_events = []

def get_event_links():
    global page_number  # To avoid re-declaring page_number in the function
    has_more_pages = True
    event_links = []
    
    while has_more_pages:
        soup = get_page_html(page_number)
        event_list = soup.find_all("a", class_="b-link b-link_style_black")
        
        if event_list:
            for event in event_list:
                event_name = event.text.strip()
                event_url = event['href']
                event_links.append(event_url)
                all_events.append({"event_name": event_name, "event_url": event_url})
            
            page_number += 1  # Move to the next page
           
        else:
            has_more_pages = False
    
    return event_links

def get_fight_data(event_url):
    fights = []
    event_response = requests.get(event_url)
    events_df = pd.DataFrame(all_events)
    for index, row in events_df.iterrows():
        event_name = row['event_name']
        event_url = row['event_url']
        
        # Request the event page
        event_response = requests.get(event_url)
        event_soup = BeautifulSoup(event_response.content, "html.parser")
        
       
        fight_table = event_soup.find("tbody")
          
        if fight_table:
                for row in fight_table.find_all("tr"):
                    fighters = row.find_all("td")
        
                    if len(fighters) >= 10:  
                        try:
                            fighter_1 = fighters[1].find_all("p")[0].text.strip() if len(fighters[1].find_all("p")) > 0 else "Unknown"
                            fighter_2 = fighters[1].find_all("p")[1].text.strip() if len(fighters[1].find_all("p")) > 1 else "Unknown"
                            result = fighters[0].text.strip()
                            method = fighters[7].text.strip() if len(fighters) > 7 else "N/A"
                            round_ = fighters[8].text.strip() if len(fighters) > 8 else "N/A"
                            time_ = fighters[9].text.strip() if len(fighters) > 9 else "N/A"
    
                            fights.append({
                                "event": event_name,
                                "fighter_1": fighter_1,
                                "fighter_2": fighter_2,
                                "result": result,
                                "method": method,
                                "round": round_,
                                "time": time_
                            })
                        except Exception as e:
                            print(f"Error parsing fight row: {e}")
    return fights

def collect_all_fights():
    all_fights = []
    event_links = get_event_links()  
    
    for event_url in event_links:
        event_fights = get_fight_data(event_url)
        all_fights.extend(event_fights)
    
    return all_fights

all_fights = collect_all_fights()


df = pd.DataFrame(all_fights)
df.to_csv("ufc_all_fight_data_csv", index=False)
print("ufc_all_fight_data_csv.csv saved successfully")
