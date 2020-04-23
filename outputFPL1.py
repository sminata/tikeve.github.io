#!/usr/bin/env python
# coding: utf-8

# In[5]:


import constti
import inputFPL1
import Brr_functions
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import numpy as np
from pathlib import Path
from inputFPL1 import inputFPL

#Table, Fixtures, Teams, Players = inputFPL()
def outputFPL():
    
    Table = pd.read_csv('in/Table.csv')
    Fixtures = pd.read_csv('in/Fixtures.csv')
    Teams = pd.read_csv('in/Teams.csv')
    Players = pd.read_csv('in/Players.csv')
    
    #Teams in Premier League
    team_number = len(Teams)
    
    #Calculating last gameweek with at least one game played
    firstr = len(Fixtures)+1
    lastr = 0
    for i in range(len(Fixtures)):
        if Fixtures.at[i,'finished']==True:
            firstr = min(firstr, i)
            lastr = i
    if firstr < len(Fixtures)+1:
        lastGW = int(Fixtures.at[lastr,'event'])
    else: lastGW = 0
    if lastr == len(Fixtures):
        lastGW = int(Fixtures.at[lastr,'event'])

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

    #Kills unfinished matches
    def is_finished(n):
        if n=='':
            return False
        else:
            a = Fixtures[Fixtures['id']==n]['finished']
            #print(a)
            return a.bool()







    #Fixtures
    Team_fixtures = pd.DataFrame()
    for j in range(lastGW,0,-1): 
        Team_fixtures['GW'+str(j)] = [Fixtures[((Fixtures['team_a']==i)|(Fixtures['team_h']==i))&                                    (Fixtures['event']==j)]['id'].values for i in range(1, team_number+1)]

    Player_fixtures = pd.DataFrame()
    for j in range(lastGW,0,-1): 
        Player_fixtures['GW'+str(j)] = [Table[(Table['element']==i)&                                    (Table['round']==j)]['fixture'].values for i in Players['id']]


    #Team tables

    print(0)
    #1. Creating  a table with average threat and GW threats for teams

    TeamThreat = Teams.copy()
    TeamThreat.columns = ['id', 'Teams', 'Threat av', 'Matches']

    for j in range(lastGW,0,-1):
        TeamThreat['Threat GW'+str(j)] = [[] for _ in range(team_number)]
        for i in range(team_number):
            for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                TeamThreat.at[i,'Threat GW'+str(j)].append(Table[(Table['fixture']==Team_fixtures.at[i, 'GW'+str(j)][k])&                                                               (Table['team']==i+1)]['threat'].sum())


    TeamThreat['Threat av'] = [Table[Table['team']==i]['threat'].sum() for i in range(1,team_number+1)]         /noZ(Teams['Matches'])
    TeamThreat.sort_values('Threat av', ascending = False, inplace = True)

    print(1)
    #2. Creating  a table with average creativity and GW creativities for teams

    TeamCreativity = Teams.copy()
    TeamCreativity.columns = ['id', 'Teams', 'Creativity av', 'Matches']

    for j in range(lastGW,0,-1):
        TeamCreativity['Creativity GW'+str(j)] = [[] for _ in range(team_number)]
        for i in range(team_number):
            for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                TeamCreativity.at[i,'Creativity GW'+str(j)].append(Table[(Table['fixture']==Team_fixtures.at[i, 'GW'+str(j)][k])&                                                               (Table['team']==i+1)]['creativity'].sum())


    TeamCreativity['Creativity av'] = [Table[Table['team']==i]['creativity'].sum() for i in range(1,team_number+1)]         /noZ(Teams['Matches'])
    print(2)
    #3. Creating  a table with average threat allowed by teams and GW threat allowed

    TableDefence = Teams.copy()
    TableDefence.columns = ['id', 'Teams', 'Threat allowed av', 'Matches']

    for j in range(lastGW,0,-1):
        TableDefence['Threat allowed GW'+str(j)] = [[] for _ in range(team_number)]
        for i in range(team_number):
            for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                TableDefence.at[i,'Threat allowed GW'+str(j)].append(Table[(Table['fixture']==                     Team_fixtures.at[i, 'GW'+str(j)][k])&(Table['opponent_team']==i+1)]['threat'].sum())


    TableDefence['Threat allowed av'] = [Table[Table['opponent_team']==i]['threat'].sum() for i in range(1,team_number+1)]             /noZ(Teams['Matches'])

    threatAllowedAv = TableDefence['Threat allowed av'].mean()
    print(3)
    #4. Creating  a table with average adjusted threat and GW threats adj for teams

    TeamThreatAd = Teams.copy()
    TeamThreatAd.columns = ['id', 'Teams', 'Threat av adj', 'Matches']

    for j in range(lastGW,0,-1):
        TeamThreatAd['Threat GW'+str(j)+' adj'] = [[] for _ in range(team_number)]
        for i in range(team_number):
            for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                if toint(Fixtures[Fixtures['id']==Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==i+1:
                    TeamThreatAd.at[i,'Threat GW'+str(j)+' adj'].append(TeamThreat.at[i,'Threat GW'+str(j)][k]*threatAllowedAv/                         TableDefence.at[toint(Fixtures[Fixtures['id']==                        Team_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                else:
                      TeamThreatAd.at[i,'Threat GW'+str(j)+' adj'].append(TeamThreat.at[i,'Threat GW'+str(j)][k]*threatAllowedAv/                        TableDefence.at[toint(Fixtures[Fixtures['id']==                        Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                TeamThreatAd.at[i,'Threat av adj'] = TeamThreatAd.at[i,'Threat av adj']  +                     TeamThreatAd.at[i,'Threat GW'+str(j)+' adj'][k]


    TeamThreatAd['Threat av adj'] = TeamThreatAd['Threat av adj']/noZ(Teams['Matches'])
    print(4)
    #5. Creating  a table with average adjusted creativity and GW creativities adj for teams

    TeamCreativityAd = Teams.copy()
    TeamCreativityAd.columns = ['id', 'Teams', 'Creativity av adj', 'Matches']

    for j in range(lastGW,0,-1):
        TeamCreativityAd['Creativity GW'+str(j)+' adj'] = [[] for _ in range(team_number)]
        for i in range(team_number):
            for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                if toint(Fixtures[Fixtures['id']==Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==i+1:
                    TeamCreativityAd.at[i,'Creativity GW'+str(j)+' adj'].append(TeamCreativity.at[i,'Creativity GW'+str(j)][k]*                        threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                        Team_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                else:
                      TeamCreativityAd.at[i,'Creativity GW'+str(j)+' adj'].append(TeamCreativity.at[i,'Creativity GW'+str(j)][k]*                        threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                        Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                TeamCreativityAd.at[i,'Creativity av adj'] = TeamCreativityAd.at[i,'Creativity av adj']  +                     TeamCreativityAd.at[i,'Creativity GW'+str(j)+' adj'][k]


    TeamCreativityAd['Creativity av adj'] = TeamCreativityAd['Creativity av adj']/noZ(Teams['Matches'])
    print(5)
    #6. Creating  a table with average threat allowed adjusted by teams and GW threat allowed adjusted

    TableDefenceAd = Teams.copy()
    TableDefenceAd.columns = ['id', 'Teams', 'Threat allowed av adj', 'Matches']

    for j in range(lastGW,0,-1):
        TableDefenceAd['Threat allowed GW'+str(j)+' adj'] = [[] for _ in range(team_number)]
        for i in range(team_number):
            for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                if toint(Fixtures[Fixtures['id']==Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==i+1:
                    TableDefenceAd.at[i,'Threat allowed GW'+str(j)+' adj'].append(TableDefence.at[i,'Threat allowed GW'+str(j)][k]*                        threatAllowedAv/TeamThreat.at[toint(Fixtures[Fixtures['id']==                        Team_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat av'])
                else:
                    TableDefenceAd.at[i,'Threat allowed GW'+str(j)+' adj'].append(TableDefence.at[i,'Threat allowed GW'+str(j)][k]*                        threatAllowedAv/TeamThreat.at[toint(Fixtures[Fixtures['id']==                        Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat av'])

                TableDefenceAd.at[i,'Threat allowed av adj'] = TableDefenceAd.at[i,'Threat allowed av adj']  +                     TableDefenceAd.at[i,'Threat allowed GW'+str(j)+' adj'][k]


    TableDefenceAd['Threat allowed av adj'] = TableDefenceAd['Threat allowed av adj']/noZ(Teams['Matches'])

    print(6)


    #Total Team Table

    TableTeams = pd.DataFrame()
    TableTeams['id'] = Teams['id']
    TableTeams['Team'] = Teams['Teams']

    TableTeams['Threat adjusted'] = TeamThreatAd['Threat av adj']
    TableTeams['Threat'] = TeamThreat['Threat av']
    TableTeams['Creativity adjusted'] = TeamCreativityAd['Creativity av adj']
    TableTeams['Creativity'] = TeamCreativity['Creativity av']
    TableTeams['Threat allowed adjusted'] = TableDefenceAd['Threat allowed av adj']
    TableTeams['Threat allowed'] = TableDefence['Threat allowed av']
    print(7)



    #PLayer Tables


    #1 Players Threat

    PlayerThreat = Players.copy()
    PlayerThreat['Threat per fixture'] = np.zeros(len(Players))
    PlayerThreat['Threat per game'] = np.zeros(len(Players))

    for j in range(lastGW,0,-1):
        PlayerThreat['Threat GW'+str(j)] = [[] for _ in range(len(Players))]
        for i in range(len(Players)):
            for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):
                PlayerThreat.at[i,'Threat GW'+str(j)].append(Table[(Table['fixture']==Player_fixtures.at[i, 'GW'+str(j)][k])&                                                               (Table['element']==PlayerThreat.at[i,'id'])]['threat'].sum())
                PlayerThreat.at[i,'Threat per game'] = PlayerThreat.at[i,'Threat per game'] +                    PlayerThreat.at[i,'Threat GW'+str(j)][k]


    PlayerThreat['Threat per fixture'] = PlayerThreat['Threat per game']/noZ(Players['Team games'])
    PlayerThreat['Threat per game'] = PlayerThreat['Threat per game']/noZ(Players['Played'])
    print(9)
    #2 Players Creativity

    PlayerCreativity = Players.copy()
    PlayerCreativity['Creativity per fixture'] = np.zeros(len(Players))
    PlayerCreativity['Creativity per game'] = np.zeros(len(Players))

    for j in range(lastGW,0,-1):
        PlayerCreativity['Creativity GW'+str(j)] = [[] for _ in range(len(Players))]
        for i in range(len(Players)):
            for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):
                PlayerCreativity.at[i,'Creativity GW'+str(j)].append(Table[(Table['fixture']==                                            Player_fixtures.at[i, 'GW'+str(j)][k])&                                            (Table['element']==PlayerCreativity.at[i,'id'])]['creativity'].sum())
                PlayerCreativity.at[i,'Creativity per game'] = PlayerCreativity.at[i,'Creativity per game'] +                    PlayerCreativity.at[i,'Creativity GW'+str(j)][k]


    PlayerCreativity['Creativity per fixture'] = PlayerCreativity['Creativity per game']/noZ(Players['Team games'])
    PlayerCreativity['Creativity per game'] = PlayerCreativity['Creativity per game']/noZ(Players['Played'])
    print(10)
    #3 Players Threat Adjusted

    PlayerThreatAd = Players.copy()
    PlayerThreatAd['Threat per fixture adj'] = np.zeros(len(Players))
    PlayerThreatAd['Threat per game adj'] = np.zeros(len(Players))

    for j in range(lastGW,0,-1):
        PlayerThreatAd['Threat GW'+str(j) + 'adj'] = [[] for _ in range(len(Players))]
        for i in range(len(Players)):
            for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):
                #If player's team is away
                if toint(Fixtures[Fixtures['id']==Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==                    PlayerThreatAd.at[i,'Team number']:
                    PlayerThreatAd.at[i,'Threat GW'+str(j) + 'adj'].append(PlayerThreat.at[i,'Threat GW'+str(j)][k]                        *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                        Player_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                #If home
                else:
                      PlayerThreatAd.at[i,'Threat GW'+str(j) + 'adj'].append(PlayerThreat.at[i,'Threat GW'+str(j)][k]
                        *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==\
                        Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                PlayerThreatAd.at[i,'Threat per game adj'] = PlayerThreatAd.at[i,'Threat per game adj'] +                    PlayerThreatAd.at[i,'Threat GW'+str(j) + 'adj'][k]


    PlayerThreatAd['Threat per fixture adj'] = PlayerThreatAd['Threat per game adj']/noZ(Players['Team games'])
    PlayerThreatAd['Threat per game adj'] = PlayerThreatAd['Threat per game adj']/noZ(Players['Played'])
    
    print(11)

    #4 PLayers Creativity Adjusted

    PlayerCreativityAd = Players.copy()
    PlayerCreativityAd['Creativity per fixture adj'] = np.zeros(len(Players))
    PlayerCreativityAd['Creativity per game adj'] = np.zeros(len(Players))

    for j in range(lastGW,0,-1):
        PlayerCreativityAd['Creativity GW'+str(j) + 'adj'] = [[] for _ in range(len(Players))]
        for i in range(len(Players)):
            for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):

                if toint(Fixtures[Fixtures['id']==Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==                    PlayerCreativityAd.at[i,'Team number']:
                    PlayerCreativityAd.at[i,'Creativity GW'+str(j) + 'adj'].append(PlayerCreativity.at[i,'Creativity GW'+str(j)][k]                        *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                        Player_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                else:
                    PlayerCreativityAd.at[i,'Creativity GW'+str(j) + 'adj'].append(PlayerCreativity.at[i,'Creativity GW'+str(j)][k]                        *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                        Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                PlayerCreativityAd.at[i,'Creativity per game adj'] = PlayerCreativityAd.at[i,'Creativity per game adj'] +                    PlayerCreativityAd.at[i,'Creativity GW'+str(j) + 'adj'][k]


    PlayerCreativityAd['Creativity per fixture adj'] = PlayerCreativityAd['Creativity per game adj']/noZ(Players['Team games'])
    PlayerCreativityAd['Creativity per game adj'] = PlayerCreativityAd['Creativity per game adj']/noZ(Players['Played'])
    print(12)


    #Tables2Files

    del TeamThreat['id']
    TeamThreat.sort_values('Threat av', ascending = False, inplace = True)
    TeamThreat.index = np.arange(1, len(TeamThreat) + 1)
    TeamThreat = Brr_functions.no_lists(TeamThreat)
    TeamThreat.to_csv(Path('out/TeamThreat.csv'))

    del TeamCreativity['id']
    TeamCreativity.sort_values('Creativity av', ascending = False, inplace = True)
    TeamCreativity.index = np.arange(1, len(TeamCreativity) + 1)
    TeamCreativity = Brr_functions.no_lists(TeamCreativity)
    TeamCreativity.to_csv(Path('out/TeamCreativity.csv'))

    del TableDefence['id']
    TableDefence.sort_values('Threat allowed av', ascending = True, inplace = True)
    TableDefence.index = np.arange(1, len(TableDefence) + 1)
    TableDefence = Brr_functions.no_lists(TableDefence)
    TableDefence.to_csv(Path('out/TableDefence.csv'))

    del TeamThreatAd['id']
    TeamThreatAd.sort_values('Threat av adj', ascending = False, inplace = True)
    TeamThreatAd.index = np.arange(1, len(TeamThreatAd) + 1)
    TeamThreatAd = Brr_functions.no_lists(TeamThreatAd)
    TeamThreatAd.to_csv(Path('out/TeamThreatAd.csv'))

    del TeamCreativityAd['id']
    TeamCreativityAd.sort_values('Creativity av adj', ascending = False, inplace = True)
    TeamCreativityAd.index = np.arange(1, len(TeamCreativityAd) + 1)
    TeamCreativityAd = Brr_functions.no_lists(TeamCreativityAd)
    TeamCreativityAd.to_csv(Path('out/TeamCreativityAd.csv'))

    del TableDefenceAd['id']
    TableDefenceAd.sort_values('Threat allowed av adj', ascending = True, inplace = True)
    TableDefenceAd.index = np.arange(1, len(TableDefenceAd) + 1)
    TableDefenceAd = Brr_functions.no_lists(TableDefenceAd)
    TableDefenceAd.to_csv(Path('out/TableDefenceAd.csv'))

    del TableTeams['id']
    TableTeams.sort_values('Threat adjusted', ascending = False, inplace = True)
    TableTeams.index = np.arange(1, len(TableTeams) + 1)
    TableTeams.to_csv(Path('out/TableTeams.csv'))

    del PlayerThreat['id']
    PlayerThreat.sort_values('Threat per fixture', ascending = False, inplace = True)
    PlayerThreat.index = np.arange(1, len(Players) + 1)
    PlayerThreat = Brr_functions.no_lists(PlayerThreat)
    PlayerThreat.to_csv(Path('out/PlayerThreat.csv'))

    del PlayerCreativity['id']
    PlayerCreativity.sort_values('Creativity per fixture', ascending = False, inplace = True)
    PlayerCreativity.index = np.arange(1, len(Players) + 1)
    PlayerCreativity = Brr_functions.no_lists(PlayerCreativity)
    PlayerCreativity.to_csv(Path('out/PlayerCreativity.csv'))

    del PlayerThreatAd['id']
    del PlayerThreatAd['Team number']
    PlayerThreatAd.sort_values('Threat per fixture adj', ascending = False, inplace = True)
    PlayerThreatAd.index = np.arange(1, len(Players) + 1)
    PlayerThreatAd = Brr_functions.no_lists(PlayerThreatAd)
    PlayerThreatAd.to_csv(Path('out/PlayerThreatAd.csv'))

    del PlayerCreativityAd['id']
    del PlayerCreativityAd['Team number']
    PlayerCreativityAd.sort_values('Creativity per fixture adj', ascending = False, inplace = True)
    PlayerCreativityAd.index = np.arange(1, len(Players) + 1)
    PlayerCreativityAd = Brr_functions.no_lists(PlayerCreativityAd)
    PlayerCreativityAd.to_csv(Path('out/PlayerCreativityAd.csv'))
    
    return TeamThreat, TeamCreativity, TableDefence, TeamThreatAd, TeamCreativityAd, TableDefenceAd, TableTeams,                PlayerThreat, PlayerCreativity, PlayerThreatAd, PlayerCreativityAd

if __name__ == '__main__':
    #Table, Fixtures, Teams, Players = inputFPL()
    TeamThreat, TeamCreativity, TableDefence, TeamThreatAd, TeamCreativityAd, TableDefenceAd, TableTeams,                PlayerThreat, PlayerCreativity, PlayerThreatAd, PlayerCreativityAd = outputFPL()
    display(PlayerThreatAd)


# In[ ]:




