from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
import pandas as pd

BASE_URL = "https://www.vegasinsider.com"
START_LINK = "/mlb/odds/las-vegas/?date=2025-05-28"
END_DATE = "2023/05/20"
MASTER_CSV = "sharma.csv"

def extract_league(url):
    path = urlparse(url).path
    return path.strip("/").split("/")[0]

def clean_odds(raw):
    return raw.replace('\n', '').replace('"', '').strip().lower().replace("even", "+100").rstrip("+")

options = webdriver.ChromeOptions()
# options.add_argument("--headless")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

link = BASE_URL + START_LINK
all_results = []

while True:
    driver.get(link)

    # Wait for date picker calendar
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "date-picker-calendar"))
    )

    # Get date
    calendar_div = driver.find_element(By.CLASS_NAME, "date-picker-calendar")
    game_date = calendar_div.get_attribute("data-date").strip()
    league = extract_league(link)

    print(f"Scraping {game_date}...")
    try:
        table = driver.find_element(By.ID, "odds-table-moneyline--0")
        rows = table.find_elements(By.TAG_NAME, "tr")
    except:
        print(f"No table found on {game_date}, skipping.")
        rows = []

    i = 0
    while i < len(rows) - 3:
        try:
            team1_row = rows[i+1]
            team2_row = rows[i+2]
            
            team1_name = team1_row.find_element(By.CLASS_NAME, "team-name").text.strip()
            team1_odds = team1_row.find_elements(By.CLASS_NAME, "game-odds")
            team1_open = clean_odds(team1_odds[0].text)
            team1_dk   = clean_odds(team1_odds[3].text)

            team2_name = team2_row.find_element(By.CLASS_NAME, "team-name").text.strip()
            team2_odds = team2_row.find_elements(By.CLASS_NAME, "game-odds")
            team2_open = clean_odds(team2_odds[0].text)
            team2_dk   = clean_odds(team2_odds[3].text)

            all_results.append([
                game_date, league,
                team1_name, team2_name,
                team1_open, team1_dk,
                team2_open, team2_dk
            ])
        except Exception as e:
            print(f"Game parse error at {i}: {e}")
        i += 4

    # Stop if we've hit the end date
    if game_date <= END_DATE:
        print("Reached end date.")
        break

    # Navigate to the previous date via calendar tabs
    try:
        calendar_buttons = driver.find_elements(By.CSS_SELECTOR, '[data-role="linkable"]')
        found_next = False
        for idx, btn in enumerate(calendar_buttons):
            if "active" in btn.get_attribute("class"):
                if idx > 0:
                    prev_link = calendar_buttons[idx - 1].get_attribute("data-endpoint")
                    link = BASE_URL + prev_link
                    found_next = True
                    break
        if not found_next:
            print("No previous tab found. Ending.")
            break
    except Exception as e:
        print(f"Calendar nav error: {e}")
        break

# Write to single file
driver.quit()

if all_results:
    df = pd.DataFrame(all_results, columns=["Date", "League", "Team1", "Team2", "T1 Open", "T1 DK", "T2 Open", "T2 DK"])
    df.to_csv(MASTER_CSV, index=False)
    print(f"✅ Saved all data to {MASTER_CSV}")
else:
    print("⚠️ No data scraped.")