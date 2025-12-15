import requests
import pandas as pd
from datetime import datetime
import os
import time

# --- GET KEY FROM GITHUB SECRETS ---
API_KEY = os.environ["ODDS_API_KEY"]

# CONFIGURATION
FILE_NAME = "prop_log.csv"
SPORTS_CONFIG = [
    {"sport": "basketball_nba", "markets": "player_points,player_assists"},
    {"sport": "icehockey_nhl", "markets": "player_points,player_goals"},
    {"sport": "americanfootball_nfl", "markets": "player_rush_yds,player_pass_yds"}
]

def run_scraper():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"--- RUN START: {timestamp} ---")
    
    new_data = []

    for config in SPORTS_CONFIG:
        sport = config['sport']
        print(f"Scanning {sport}...")
        
        try:
            # 1. Get Schedule
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/events"
            res = requests.get(url, params={"apiKey": API_KEY, "regions": "us"})
            
            if res.status_code != 200:
                print(f"Skipping {sport}: API Status {res.status_code}")
                continue
                
            events = res.json()
            
            # 2. Get Odds
            for game in events:
                game_id = game['id']
                odds_url = f"https://api.the-odds-api.com/v4/sports/{sport}/events/{game_id}/odds"
                params = {
                    "apiKey": API_KEY, "regions": "us", 
                    "markets": config['markets'], "oddsFormat": "american"
                }
                
                odds_res = requests.get(odds_url, params=params)
                if odds_res.status_code != 200: continue
                
                # Parse
                for book in odds_res.json().get('bookmakers', []):
                    for market in book.get('markets', []):
                        for outcome in market['outcomes']:
                            new_data.append({
                                'Log_Time': timestamp,
                                'Sport': sport,
                                'Game': f"{game['away_team']} @ {game['home_team']}",
                                'Player': outcome.get('description'),
                                'Prop': market['key'],
                                'Book': book['title'],
                                'Line': outcome.get('point'),
                                'Odds': outcome.get('price')
                            })
                time.sleep(0.1) # Be nice to API limits
        except Exception as e:
            print(f"Error on {sport}: {e}")
            continue

    # 3. Save to CSV
    if new_data:
        df_new = pd.DataFrame(new_data)
        
        # Check if file exists in the repo to append
        if os.path.exists(FILE_NAME):
            df_old = pd.read_csv(FILE_NAME)
            df_final = pd.concat([df_old, df_new], ignore_index=True)
        else:
            df_final = df_new
            
        df_final.to_csv(FILE_NAME, index=False)
        print(f"✅ Successfully logged {len(df_new)} new lines.")
    else:
        print("❌ No data found this run.")

if __name__ == "__main__":
    run_scraper()
