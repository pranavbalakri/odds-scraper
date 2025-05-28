import openpyxl
#INPUT THE SPREADSHEET PATH HERE
data = ''
sheet1_name = ''
date = 'a'
from Devigger import devigger


devigger(-110,-110,'american')
wb = openpyxl.load_workbook(data)
sheet = wb[sheet1_name]

def kelly(fraction, probability, odds):
    return fraction*(probability*odds-1)/(odds-1)

def strategy_1(sheet):
    #This strategy uniformly buys the moneyline for which the ending line move towards, betting either to win 1 unit if the team is a favorite or betting 1 unit if the team is an underdog
    devigbankroll = 100
    bankroll = 100
    for row in sheet.iter_rows(values_only=True):
        team_1_opening_odds = row[7]
        team_1_closing_odds = row[10]
        team_2_opening_odds = row[12]
        team_2_closing_odds = row[15]
        odds_difference = devigger(team_1_opening_odds, team_2_opening_odds, 'american')[1] - devigger(team_1_opening_odds, team_2_opening_odds, 'american')[2] - (devigger(team_1_closing_odds, team_2_closing_odds, 'american')[1] - devigger(team_1_closing_odds, team_2_closing_odds, 'american')[2])
        score_difference = row[16] - row[17]
        if odds_difference > 0:
            #we are betting on team 1, since the odds have moved in their favor
            if score_difference > 0:
                #a positive score difference means team 1 won
                if team_1_closing_odds > 0:
                    bankroll += 1*(team_1_closing_odds/100)
                    devigbankroll += 1*devigger(team_1_closing_odds, team_2_closing_odds, 'american')[1]/100
                if team_1_closing_odds < 0:
                    bankroll += 1
                    devigbankroll += 1/devigger(team_1_closing_odds, team_2_closing_odds, 'american')[1]
            else:
                if team_1_closing_odds > 0:
                    bankroll -= 1/(100/(-1*team_1_closing_odds))
                    devigbankroll -= 1/(100/(-1*devigger(team_1_closing_odds, team_2_closing_odds, 'american')[1]))
        if odds_difference < 0:
            #we are betting on team 2, since the odds have moved in their favor
            if score_difference < 0:
                #a negative score difference means team 2 won
                if team_2_closing_odds > 0:
                    bankroll += 1*(team_2_closing_odds/100)
                    devigbankroll += 1*devigger(team_2_closing_odds, team_1_closing_odds, 'american')[1]/100
                if team_2_closing_odds < 0:
                    bankroll += 1
                    devigbankroll += 1/devigger(team_2_closing_odds, team_1_closing_odds, 'american')[1]
            else:
                if team_2_closing_odds > 0:
                    bankroll -= 1/(100/(-1*team_2_closing_odds))
                    devigbankroll -= 1/(100/(-1*devigger(team_2_closing_odds, team_1_closing_odds, 'american')[1]))






    



