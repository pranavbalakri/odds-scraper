from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse
from datetime import datetime
import pandas as pd
import time

BASE_URL = "https://www.vegasinsider.com"
START_LINK = "/mlb/odds/las-vegas/?date=2025-05-29"
END_DATE = "2023/05/26"
MASTER_CSV = "sharmanator.csv"

def extract_league(url):
    path = urlparse(url).path
    return path.strip("/").split("/")[0]

def clean_odds(raw):
    return raw.replace('\n', '').replace('"', '').strip().lower().replace("even", "+100").rstrip("+")

def normalize_team_name(name):
    return name.lower().replace(" ", "").replace("-", "")

def normalize_slug(name):
    return name.lower().replace(" ", "-").replace(".", "").replace("@", "").replace("(", "").replace(")", "").strip()

def get_game_outcome(driver, game_date, team1, team2):
    try:
        team1_slug = normalize_slug(team1)
        team2_slug = normalize_slug(team2)
        matchup_url = f"{BASE_URL}/mlb/matchups/{team1_slug}-vs-{team2_slug}/"

        driver.execute_script("window.open(arguments[0]);", matchup_url)
        driver.switch_to.window(driver.window_handles[1])

        time.sleep(1)
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "schedule-table")))
        rows = driver.find_elements(By.CSS_SELECTOR, ".schedule-table tbody tr")

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            if len(tds) >= 5:
                raw_date = tds[0].text.strip()
                try:
                    parsed_date = datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y/%m/%d")
                except:
                    continue
                if parsed_date != game_date:
                    continue

                team = tds[1].text.strip()
                opp = tds[2].text.strip().replace("@", "").strip()
                result = tds[4].text.strip().lower()

                if "won" in result:
                    winner = team
                elif "lost" in result:
                    winner = opp
                else:
                    winner = "N/A"

                driver.close()
                driver.switch_to.window(driver.window_handles[0])
                return winner
    except Exception as e:
        print(f"Matchup error for {team1} vs {team2}: {e}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        return "N/A"

    return "N/A"

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

link = BASE_URL + START_LINK
all_results = []
first_day = True

while True:
    driver.get(link)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "date-picker-calendar"))
    )

    calendar_div = driver.find_element(By.CLASS_NAME, "date-picker-calendar")
    game_date = calendar_div.get_attribute("data-date").strip()
    league = extract_league(link)

    print(f"\n📅 Scraping {game_date}...")
    try:
        table = driver.find_element(By.ID, "odds-table-moneyline--0")
        rows = table.find_elements(By.TAG_NAME, "tr")
    except:
        print("⚠️ No table found, skipping.")
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

            if first_day:
                outcome = "N/A"
            else:
                outcome = get_game_outcome(driver, game_date, team1_name, team2_name)

            all_results.append([
                game_date, league,
                team1_name, team2_name,
                team1_open, team1_dk,
                team2_open, team2_dk,
                outcome
            ])
        except Exception as e:
            print(f"Game error at row {i}: {e}")
        i += 4

    first_day = False  # Future dates skipped only once

    if game_date <= END_DATE:
        print("Reached end date.")
        break

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
            print("No previous date available")
            break
    except Exception as e:
        print(f"Calendar navigation error: {e}")
        break

driver.quit()

# Save combined data
if all_results:
    df = pd.DataFrame(all_results, columns=["Date", "League", "Team1", "Team2", "T1 Open", "T1 DK", "T2 Open", "T2 DK", "Outcome"])
    df.to_csv(MASTER_CSV, index=False)
    print(f"\n All data saved to {MASTER_CSV}")
else:
    print("No data collected")
