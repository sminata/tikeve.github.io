#!/usr/bin/env python
# coding: utf-8

# In[1]:


from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import numpy as np
from pathlib import Path

team_number = 20
url1 = "https://fantasy.premierleague.com/api/bootstrap-static/"
url2 = "https://fantasy.premierleague.com/api/entry/698498/history/"
url3 = "https://fantasy.premierleague.com/api/event/6/live/"
url4 = "https://fantasy.premierleague.com/api/fixtures"

#NaNs to zeros
def toint(a):
    if np.isnan(a):
        return 0
    else: return int(a)

#If no matches played not to devide by zero
def noZ(a):
    b = a.copy()
    for i in range(len(b)):
        if b[i] == 0:
            b[i]=1
    return b


p1 = requests.get(url1)
#page1 = BeautifulSoup(p1.text)
#data1 = str(page1.p)[3:-4]
data1 = p1.text

d1 = json.loads(data1)
bigTable = pd.DataFrame(d1['elements'])
bigTable = bigTable[['team', 'element_type', 'web_name', 'goals_scored', 'assists', 'bonus', 'event_points', 'total_points', 
               'saves', 'own_goals', 'clean_sheets', 'penalties_missed', 'penalties_saved', 'yellow_cards', 'red_cards', 
               'minutes', 'bps', 'creativity', 'threat', 'ict_index', 'influence',
               'value_season', 'form', 'value_form', 'points_per_game', 
               'goals_conceded', 
               'in_dreamteam', 'dreamteam_count',
               'now_cost', 'cost_change_event', 'cost_change_event_fall',
               'cost_change_start', 'cost_change_start_fall', 'selected_by_percent',
               'transfers_in_event', 'transfers_out_event', 'transfers_in', 'transfers_out', 
               'chance_of_playing_this_round', 'chance_of_playing_next_round', 'news_added', 'news', 'status', 
               'ep_this', 'ep_next', 'first_name', 'second_name', 'team_code', 'id', 'photo', 'special', 'squad_number', 'code']]
bigTable['full_name'] = bigTable['first_name'] + ' ' + bigTable['second_name']
bigTable.to_csv(Path('in/fpltable.csv'))

p4 = requests.get(url4)
#page4 = BeautifulSoup(p4.text)
#data4 = str(page4.p)[3:-4]
d4 = json.loads(p4.text)
Fixtures = pd.DataFrame(d4)
Fixtures.to_csv(Path('in/fplfixtures.csv'))

#Figuring out ended lastGameweek   lastGW

if Fixtures.at[1,'minutes'] != 90:
    lastGW = 0
elif Fixtures.at[len(Fixtures)-1,'minutes'] == 90:
    lastGW = Fixtures.at[len(Fixtures)-1,'event']
else:
    for i in range(1,len(Fixtures)):
        if Fixtures.at[i,'minutes'] != 90:
            lastGW = Fixtures.at[i-1,'event']
            break
lastGW = int(lastGW)

Gameweeks = pd.DataFrame()
for i in range(1,2*team_number - 1):
    url = "https://fantasy.premierleague.com/api/event/" + str(i) + "/live/"
    p = requests.get(url)
    #page = BeautifulSoup(p.text)
    #data = str(page.p)[3:-4]
    d = json.loads(p.text)
    nexTour = pd.DataFrame(d['elements'])
    
    if not nexTour.empty:
        nt1 = pd.DataFrame(nexTour['stats'].tolist())
        nt1['id'] = nexTour['id']
        nt1['gameweek'] = i
        nt1.index = nt1['gameweek']*1000+nt1['id']
        Gameweeks = Gameweeks.append(nt1)
        print(i)


teams = dict(zip(pd.DataFrame(d1['teams'])['id'],pd.DataFrame(d1['teams'])['name']))
players = dict(zip(bigTable['id'],bigTable['full_name']))
teamplayers = dict(zip(bigTable['id'],bigTable['team']))

Gameweeks['team'] = [teamplayers[i] for i in Gameweeks['id']]

Gameweeks['threat'] = pd.to_numeric(Gameweeks['threat'])
Gameweeks['creativity'] = pd.to_numeric(Gameweeks['creativity'])

Gameweeks['team_a'] = [int(Fixtures[(Fixtures['event'] == Gameweeks.iloc[i,20]) &                                          ((Fixtures['team_a'] == Gameweeks.iloc[i,21])|                                          (Fixtures['team_h'] == Gameweeks.iloc[i,21]))]['team_a'])                             for i in range(len(Gameweeks))]
Gameweeks['team_h'] = [int(Fixtures[(Fixtures['event'] == Gameweeks.iloc[i,20]) &                                          ((Fixtures['team_a'] == Gameweeks.iloc[i,21])|                                          (Fixtures['team_h'] == Gameweeks.iloc[i,21]))]['team_h'])                             for i in range(len(Gameweeks))]

Gameweeks['teamAgainst'] = [Gameweeks.at[i,'team_a'] if Gameweeks.at[i,'team'] == Gameweeks.at[i,'team_h']                            else Gameweeks.at[i,'team_h']                            for i in Gameweeks.index]
Gameweeks['side'] = ['home' if Gameweeks.at[i,'team'] == Gameweeks.at[i,'team_h']                            else 'away'                            for i in Gameweeks.index]

del Gameweeks['team_a']
del Gameweeks['team_h']


Gameweeks.to_csv(Path('in/fplgameweeks.csv'))
Gameweeks



#Team tables

print(0)
#1. Creating  a table with average threat and GW threats for teams

TeamThreat = pd.DataFrame()
TeamThreat['id'] = pd.DataFrame(d1['teams'])['id']
TeamThreat['Team'] = pd.DataFrame(d1['teams'])['name']
TeamThreat['Threat av'] = np.zeros(len(TeamThreat))
TeamThreat['Matches'] = np.zeros(len(TeamThreat))

for j in range(lastGW,0,-1):
    TeamThreat['Threat GW'+str(j)] = [Gameweeks[(Gameweeks['team']==i)&(Gameweeks['gameweek']==j)]['threat'].sum()                                       for i in range(1,team_number+1)]
    TeamThreat['Matches'] = TeamThreat['Matches'] + (TeamThreat['Threat GW'+str(j)] != np.zeros(len(TeamThreat)))
    

TeamThreat['Threat av'] = [Gameweeks[Gameweeks['team']==i]['threat'].sum() for i in range(1,team_number+1)]     /noZ(TeamThreat['Matches'])
print(1)
#2. Creating  a table with average creativity and GW creativities for teams

TeamCreativity = pd.DataFrame()
TeamCreativity['id'] = pd.DataFrame(d1['teams'])['id']
TeamCreativity['Team'] = pd.DataFrame(d1['teams'])['name']
TeamCreativity['Creativity av'] = np.zeros(len(TeamCreativity))
TeamCreativity['Matches'] = np.zeros(len(TeamCreativity))

for j in range(lastGW,0,-1):
    TeamCreativity['Creativity GW'+str(j)] = [Gameweeks[(Gameweeks['team']==i)&(Gameweeks['gameweek']==j)]             ['creativity'].sum() for i in range(1,team_number+1)]
    TeamCreativity['Matches'] = TeamCreativity['Matches'] +             (TeamCreativity['Creativity GW'+str(j)] != np.zeros(len(TeamCreativity)))
    

TeamCreativity['Creativity av'] = [Gameweeks[Gameweeks['team']==i]['creativity'].sum() for i in range(1,team_number+1)]         /noZ(TeamCreativity['Matches'])
print(2)
#3. Creating  a table with average threat allowed by teams and GW threat allowed

TableDefence = pd.DataFrame()
TableDefence['id'] = pd.DataFrame(d1['teams'])['id']
TableDefence['Team'] = pd.DataFrame(d1['teams'])['name']
TableDefence['Threat allowed av'] = np.zeros(len(TableDefence))
TableDefence['Matches'] = np.zeros(len(TableDefence))

for j in range(lastGW,0,-1):
    TableDefence['Threat allowed GW'+str(j)] = [Gameweeks[(Gameweeks['teamAgainst']==i)&(Gameweeks['gameweek']==j)]             ['threat'].sum() for i in range(1,team_number+1)]
    TableDefence['Matches'] = TableDefence['Matches'] +             (TableDefence['Threat allowed GW'+str(j)] != np.zeros(len(TableDefence)))

TableDefence['Threat allowed av'] = [Gameweeks[Gameweeks['teamAgainst']==i]['threat'].sum() for i in range(1,team_number+1)]         /noZ(TableDefence['Matches'])

threatAllowedAv = TableDefence['Threat allowed av'].mean()
print(3)
#4. Creating  a table with average adjusted threat and GW threats adj for teams

TeamThreatAd = pd.DataFrame()
TeamThreatAd['id'] = pd.DataFrame(d1['teams'])['id']
TeamThreatAd['Team'] = pd.DataFrame(d1['teams'])['name']
TeamThreatAd['Threat av adj'] = np.zeros(len(TeamThreatAd))
TeamThreatAd['Matches'] = np.zeros(len(TeamThreatAd))

for j in range(lastGW,0,-1):    
    TeamThreatAd['Threat GW'+str(j)+' adj'] = [TeamThreat.at[i-1,'Threat GW'+str(j)]*threatAllowedAv/                 TableDefence.at[int(Gameweeks[(Gameweeks['team']==i)&(Gameweeks['gameweek']==j)]['teamAgainst'].mean()-1),                 'Threat allowed av']                                              for i in range(1,team_number+1)]
    TeamThreatAd['Matches'] = TeamThreatAd['Matches'] + (TeamThreatAd['Threat GW'+str(j)+' adj'] != np.zeros(len(TeamThreat)))
    TeamThreatAd['Threat av adj'] = TeamThreatAd['Threat av adj']  + TeamThreatAd['Threat GW'+str(j)+' adj']

TeamThreatAd['Threat av adj'] = TeamThreatAd['Threat av adj']/noZ(TeamThreatAd['Matches'])
print(4)
#5. Creating  a table with average adjusted creativity and GW creativities adj for teams

TeamCreativityAd = pd.DataFrame()
TeamCreativityAd['id'] = pd.DataFrame(d1['teams'])['id']
TeamCreativityAd['Team'] = pd.DataFrame(d1['teams'])['name']
TeamCreativityAd['Creativity av adj'] = np.zeros(len(TeamCreativityAd))
TeamCreativityAd['Matches'] = np.zeros(len(TeamCreativityAd))

for j in range(lastGW,0,-1):    
    TeamCreativityAd['Creativity GW'+str(j)+' adj'] = [TeamCreativity.at[i-1,'Creativity GW'+str(j)]*threatAllowedAv/                 TableDefence.at[int(Gameweeks[(Gameweeks['team']==i)&(Gameweeks['gameweek']==j)]['teamAgainst'].mean()-1),                 'Threat allowed av']                                              for i in range(1,team_number+1)]
    TeamCreativityAd['Matches'] = TeamCreativityAd['Matches'] + (TeamCreativityAd['Creativity GW'+str(j)+' adj'] !=                                                                  np.zeros(len(TeamCreativity)))
    TeamCreativityAd['Creativity av adj'] = TeamCreativityAd['Creativity av adj']  +         TeamCreativityAd['Creativity GW'+str(j)+' adj']

TeamCreativityAd['Creativity av adj'] = TeamCreativityAd['Creativity av adj']/noZ(TeamThreatAd['Matches'])
print(5)
#6. Creating  a table with average threat allowed adjusted by teams and GW threat allowed adjusted

TableDefenceAd = pd.DataFrame()
TableDefenceAd['id'] = pd.DataFrame(d1['teams'])['id']
TableDefenceAd['Team'] = pd.DataFrame(d1['teams'])['name']
TableDefenceAd['Threat allowed av adj'] = np.zeros(len(TableDefenceAd))
TableDefenceAd['Matches'] = np.zeros(len(TableDefenceAd))

for j in range(lastGW,0,-1):    
    TableDefenceAd['Threat allowed GW'+str(j)+' adj'] = [TableDefence.at[i-1,'Threat allowed GW'+str(j)]*threatAllowedAv/                 TeamThreat.at[int(Gameweeks[(Gameweeks['team']==i)&(Gameweeks['gameweek']==j)]['teamAgainst'].mean()-1),                 'Threat av']                                              for i in range(1,team_number+1)]
    TableDefenceAd['Matches'] = TableDefenceAd['Matches'] + (TableDefenceAd['Threat allowed GW'+str(j)+' adj'] !=                                                                  np.zeros(len(TableDefenceAd)))
    TableDefenceAd['Threat allowed av adj'] = TableDefenceAd['Threat allowed av adj']  +         TableDefenceAd['Threat allowed GW'+str(j)+' adj']

TableDefenceAd['Threat allowed av adj'] = TableDefenceAd['Threat allowed av adj']/noZ(TableDefenceAd['Matches'])

print(6)


#Total Team Table

TableTeams = pd.DataFrame()
TableTeams['id'] = pd.DataFrame(d1['teams'])['id']
TableTeams['Team'] = pd.DataFrame(d1['teams'])['name']

TableTeams['Threat adjusted'] = TeamThreatAd['Threat av adj']
TableTeams['Threat'] = TeamThreat['Threat av']
TableTeams['Creativity adjusted'] = TeamCreativityAd['Creativity av adj']
TableTeams['Creativity'] = TeamCreativity['Creativity av']
TableTeams['Threat allowed adjusted'] = TableDefenceAd['Threat allowed av adj']
TableTeams['Threat allowed'] = TableDefence['Threat allowed av']
print(7)



#PLayer Tables

#PlayerMatches = pd.DataFrame(list(players.keys()), columns = ['id'])
PlayerMatches = pd.DataFrame()
PlayerMatches['id'] = bigTable['id']
PlayerMatches['Team number'] = [bigTable[bigTable['id'] == i]['team'].sum() for i in players.keys()]
PlayerMatches['Team'] = [teams[PlayerMatches.at[i,'Team number']] for i in range(len(players))]
PlayerMatches['Team games'] = np.zeros(len(players))
PlayerMatches['Played'] = np.zeros(len(players))

for j in range(lastGW,0,-1):
    PlayerMatches['Played'] = PlayerMatches['Played'] + ([Gameweeks[(Gameweeks['id']==PlayerMatches.iat[i,0])&                                    (Gameweeks['gameweek']==j)]['minutes'].sum()                                     for i in range(len(PlayerMatches))] != np.zeros(len(PlayerMatches)))

PlayerMatches['Team games'] = PlayerMatches['Team games'] + [len(Gameweeks[Gameweeks['id']==PlayerMatches.iat[i,0]])                                    for i in range(len(PlayerMatches))]
print(8)
#1 Players Threat

PlayerThreat = pd.DataFrame()
PlayerThreat['id'] = bigTable['id']
PlayerThreat['Name'] = bigTable['full_name']
PlayerThreat['Team'] = PlayerMatches['Team']
PlayerThreat['Threat per fixture'] = np.zeros(len(players))
PlayerThreat['Threat per game'] = np.zeros(len(players))

for j in range(lastGW,0,-1):
    PlayerThreat['Threat GW'+str(j)] = [Gameweeks[(Gameweeks['id']==PlayerThreat.iat[i,0])&(Gameweeks['gameweek']==j)]                                     ['threat'].sum()                                     for i in range(len(players))]
    PlayerThreat['Threat per game'] = PlayerThreat['Threat per game'] + PlayerThreat['Threat GW'+str(j)]

PlayerThreat['Threat per fixture'] = PlayerThreat['Threat per game']/noZ(PlayerMatches['Team games'])
PlayerThreat['Threat per game'] = PlayerThreat['Threat per game']/noZ(PlayerMatches['Played'])
print(9)
#2 Players Creativity

PlayerCreativity = pd.DataFrame()
PlayerCreativity['id'] = bigTable['id']
PlayerCreativity['Name'] = bigTable['full_name']
PlayerCreativity['Team'] = PlayerMatches['Team']
PlayerCreativity['Creativity per fixture'] = np.zeros(len(players))
PlayerCreativity['Creativity per game'] = np.zeros(len(players))

for j in range(lastGW,0,-1):
    PlayerCreativity['Creativity GW'+str(j)] = [Gameweeks[(Gameweeks['id']==PlayerThreat.iat[i,0])&                    (Gameweeks['gameweek']==j)]['creativity'].sum() for i in range(len(players))]
    PlayerCreativity['Creativity per game'] = PlayerCreativity['Creativity per game']        + PlayerCreativity['Creativity GW'+str(j)]

PlayerCreativity['Creativity per fixture'] = PlayerCreativity['Creativity per game']/noZ(PlayerMatches['Team games'])
PlayerCreativity['Creativity per game'] = PlayerCreativity['Creativity per game']/noZ(PlayerMatches['Played'])
print(10)
#3 Players Threat Adjusted

PlayerThreatAd = pd.DataFrame()
PlayerThreatAd['id'] = bigTable['id']
PlayerThreatAd['Name'] = bigTable['full_name']
PlayerThreatAd['Team number'] = PlayerMatches['Team number']
PlayerThreatAd['Team'] = PlayerMatches['Team']
PlayerThreatAd['Threat per fixture adj'] = np.zeros(len(players))
PlayerThreatAd['Threat per game adj'] = np.zeros(len(players))
for j in range(lastGW,0,-1):
        
    PlayerThreatAd['Threat GW'+str(j) + 'adj'] = [PlayerThreat.at[i,'Threat GW'+str(j)]*threatAllowedAv/             TableDefence.at[toint(Gameweeks[(Gameweeks['team']==PlayerThreatAd.at[i,'Team number'])&            (Gameweeks['gameweek']==j)]['teamAgainst'].mean()-1),             'Threat allowed av']  for i in range(len(players))]                     
    
    PlayerThreatAd['Threat per game adj'] = PlayerThreatAd['Threat per game adj'] +            PlayerThreatAd['Threat GW'+str(j) + 'adj']
PlayerThreatAd['Threat per fixture adj'] = PlayerThreatAd['Threat per game adj']/noZ(PlayerMatches['Team games'])
PlayerThreatAd['Threat per game adj'] = PlayerThreatAd['Threat per game adj']/noZ(PlayerMatches['Played'])
print(11)

#4 PLayers Creativity Adjusted

PlayerCreativityAd = pd.DataFrame()
PlayerCreativityAd['id'] = bigTable['id']
PlayerCreativityAd['Name'] = bigTable['full_name']
PlayerCreativityAd['Team number'] = PlayerMatches['Team number']
PlayerCreativityAd['Team'] = PlayerMatches['Team']
PlayerCreativityAd['Creativity per fixture adj'] = np.zeros(len(players))
PlayerCreativityAd['Creativity per game adj'] = np.zeros(len(players))

for j in range(lastGW,0,-1):
        
    PlayerCreativityAd['Creativity GW'+str(j) + 'adj'] = [PlayerCreativity.at[i,'Creativity GW'+str(j)]*threatAllowedAv/             TableDefence.at[toint(Gameweeks[(Gameweeks['team']==PlayerCreativityAd.at[i,'Team number'])&                                          (Gameweeks['gameweek']==j)]['teamAgainst'].mean()-1),             'Threat allowed av']  for i in range(len(players))]                     
    
    PlayerCreativityAd['Creativity per game adj'] = PlayerCreativityAd['Creativity per game adj'] +            PlayerCreativityAd['Creativity GW'+str(j) + 'adj']

PlayerCreativityAd['Creativity per fixture adj'] = PlayerCreativityAd['Creativity per game adj']/            noZ(PlayerMatches['Team games'])
PlayerCreativityAd['Creativity per game adj'] = PlayerCreativityAd['Creativity per game adj']/            noZ(PlayerMatches['Played'])
print(12)


#Tables2Files

del TeamThreat['id']
TeamThreat.sort_values('Threat av', ascending = False, inplace = True)
TeamThreat.index = np.arange(1, len(TeamThreat) + 1)
TeamThreat.to_csv(Path('out/TeamThreat.csv'))

del TeamCreativity['id']
TeamCreativity.sort_values('Creativity av', ascending = False, inplace = True)
TeamCreativity.index = np.arange(1, len(TeamCreativity) + 1)
TeamCreativity.to_csv(Path('out/TeamCreativity.csv'))

del TableDefence['id']
TableDefence.sort_values('Threat allowed av', ascending = True, inplace = True)
TableDefence.index = np.arange(1, len(TableDefence) + 1)
TableDefence.to_csv(Path('out/TableDefence.csv'))

del TeamThreatAd['id']
TeamThreatAd.sort_values('Threat av adj', ascending = False, inplace = True)
TeamThreatAd.index = np.arange(1, len(TeamThreatAd) + 1)
TeamThreatAd.to_csv(Path('out/TeamThreatAd.csv'))

del TeamCreativityAd['id']
TeamCreativityAd.sort_values('Creativity av adj', ascending = False, inplace = True)
TeamCreativityAd.index = np.arange(1, len(TeamCreativityAd) + 1)
TeamCreativityAd.to_csv(Path('out/TeamCreativityAd.csv'))

del TableDefenceAd['id']
TableDefenceAd.sort_values('Threat allowed av adj', ascending = True, inplace = True)
TableDefenceAd.index = np.arange(1, len(TableDefenceAd) + 1)
TableDefenceAd.to_csv(Path('out/TableDefenceAd.csv'))

del TableTeams['id']
TableTeams.sort_values('Threat adjusted', ascending = False, inplace = True)
TableTeams.index = np.arange(1, len(TableTeams) + 1)
TableTeams.to_csv(Path('out/TableTeams.csv'))

del PlayerThreat['id']
PlayerThreat.sort_values('Threat per fixture', ascending = False, inplace = True)
PlayerThreat.index = np.arange(1, len(players) + 1)
PlayerThreat.to_csv(Path('out/PlayerThreat.csv'))

del PlayerCreativity['id']
PlayerCreativity.sort_values('Creativity per fixture', ascending = False, inplace = True)
PlayerCreativity.index = np.arange(1, len(players) + 1)
PlayerCreativity.to_csv(Path('out/PlayerCreativity.csv'))

del PlayerThreatAd['id']
del PlayerThreatAd['Team number']
PlayerThreatAd.sort_values('Threat per fixture adj', ascending = False, inplace = True)
PlayerThreatAd.index = np.arange(1, len(players) + 1)
PlayerThreatAd.to_csv(Path('out/PlayerThreatAd.csv'))

del PlayerCreativityAd['id']
del PlayerCreativityAd['Team number']
PlayerCreativityAd.sort_values('Creativity per fixture adj', ascending = False, inplace = True)
PlayerCreativityAd.index = np.arange(1, len(players) + 1)
PlayerCreativityAd.to_csv(Path('out/PlayerCreativityAd.csv'))

PlayerThreatAd


# In[ ]:




