#!/usr/bin/env python
# coding: utf-8

# In[21]:


import time
start = time.time()
import constti
import Brr_functions
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import numpy as np
from pathlib import Path

print('0. Import is over.\tImport takes %s sec' %  (time.time() - start))


class Source:
    def __init__(self, source):
        start = time.time()
        self.source = source
        self.ma_num = 6 # Number of matches for the moving average
        
#1. Reading nessesry data from files.
        
        Table = pd.read_csv('in/Table_'+source+'.csv') # Main data from source containing rows for each player in a game
        # with columns 'element', 'round', 'fixture', 'threat', 'creativity', 'team', opponent_team'
        Fixtures = pd.read_csv('in/Fixtures.csv') # Table of rows for each fixture
        Teams = pd.read_csv('in/Teams.csv') # Table of rows as teams with columns 'id', 'Teams', 'TARGET COL', 'Matches'
        Players = pd.read_csv('in/Players.csv') # Table of rows as players with columns 'id', 'Name', 'Team', Team games',
        # 'Played'
        del Players['web_name'] #This column is needed only for inputUnderstat.py
        
        print('1. Reading files from ' + source +' is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

#2. Defenition of useful constants and funtions
        
        #Teams in Premier League
        team_number = len(Teams)

        #Calculating lastGW - last gameweek with at least one game played
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
                return a.bool()
            
        print('2. Constants and Functions are over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

#3. Defenition of fixture matrices

        Team_fixtures = pd.DataFrame()
        for j in range(lastGW,0,-1): 
            Team_fixtures['GW'+str(j)] = [Fixtures[((Fixtures['team_a']==i)|(Fixtures['team_h']==i))&                                        (Fixtures['event']==j)]['id'].values for i in range(1, team_number+1)]

        Player_fixtures = pd.DataFrame()
        for j in range(lastGW,0,-1): 
            Player_fixtures['GW'+str(j)] = [Table[(Table['element']==i)&                                        (Table['round']==j)]['fixture'].values for i in Players['id']]
            
        print('3. Fixtures are over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

# 4. Calculating team tables

        #(1). Creating  a table with average threat and GW threats for teams

        TeamThreat = Teams.copy()
        TeamThreat.columns = ['id', 'Teams', 'Threat av', 'Matches']

        for j in range(lastGW,0,-1):
            TeamThreat['Threat GW'+str(j)] = [[] for _ in range(team_number)]
            for i in range(team_number):
                for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                    TeamThreat.at[i,'Threat GW'+str(j)].append(Table[(Table['fixture']==                                        Team_fixtures.at[i, 'GW'+str(j)][k])&(Table['team']==i+1)]['threat'].sum())


        TeamThreat['Threat av'] = [Table[Table['team']==i]['threat'].sum() for i in range(1,team_number+1)]             /noZ(Teams['Matches'])
        TeamThreat.sort_values('Threat av', ascending = False, inplace = True)

        print('4.1. TeamThreat is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()
        
        #(2). Creating  a table with average creativity and GW creativities for teams

        TeamCreativity = Teams.copy()
        TeamCreativity.columns = ['id', 'Teams', 'Creativity av', 'Matches']

        for j in range(lastGW,0,-1):
            TeamCreativity['Creativity GW'+str(j)] = [[] for _ in range(team_number)]
            for i in range(team_number):
                for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                    TeamCreativity.at[i,'Creativity GW'+str(j)].append(Table[(Table['fixture']==                                    Team_fixtures.at[i, 'GW'+str(j)][k])&(Table['team']==i+1)]['creativity'].sum())


        TeamCreativity['Creativity av'] = [Table[Table['team']==i]['creativity'].sum() for i in range(1,team_number+1)]             /noZ(Teams['Matches'])
        
        print('4.2. TeamCreativity is over.\t It takes ' + str(time.time() - start)+ ' sec')
        start = time.time()
        
        #(3). Creating  a table with average threat allowed by teams and GW threat allowed

        TableDefence = Teams.copy()
        TableDefence.columns = ['id', 'Teams', 'Threat allowed av', 'Matches']

        for j in range(lastGW,0,-1):
            TableDefence['Threat allowed GW'+str(j)] = [[] for _ in range(team_number)]
            for i in range(team_number):
                for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                    TableDefence.at[i,'Threat allowed GW'+str(j)].append(Table[(Table['fixture']==                         Team_fixtures.at[i, 'GW'+str(j)][k])&(Table['opponent_team']==i+1)]['threat'].sum())


        TableDefence['Threat allowed av'] = [Table[Table['opponent_team']==i]['threat'].sum()
                        for i in range(1,team_number+1)]/noZ(Teams['Matches'])

        threatAllowedAv = TableDefence['Threat allowed av'].mean()
        
        print('4.3. TeamDefence is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()
        
        #(4). Creating  a table with average adjusted threat and GW threats adj for teams

        TeamThreatAd = Teams.copy()
        TeamThreatAd.columns = ['id', 'Teams', 'Threat av adj', 'Matches']

        for j in range(lastGW,0,-1):
            TeamThreatAd['Threat GW'+str(j)+' adj'] = [[] for _ in range(team_number)]
            for i in range(team_number):
                for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                    if toint(Fixtures[Fixtures['id']==Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==i+1:
                        TeamThreatAd.at[i,'Threat GW'+str(j)+' adj'].append(TeamThreat.at[i,'Threat GW'+str(j)][k]*                            threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Team_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                    else:
                          TeamThreatAd.at[i,'Threat GW'+str(j)+' adj'].append(TeamThreat.at[i,'Threat GW'+str(j)][k]*                            threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                    TeamThreatAd.at[i,'Threat av adj'] = TeamThreatAd.at[i,'Threat av adj']  +                         TeamThreatAd.at[i,'Threat GW'+str(j)+' adj'][k]


        TeamThreatAd['Threat av adj'] = TeamThreatAd['Threat av adj']/noZ(Teams['Matches'])
        
        print('4.4. TeamThreatAd is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()
        
        #(5). Creating  a table with average adjusted creativity and GW creativities adj for teams

        TeamCreativityAd = Teams.copy()
        TeamCreativityAd.columns = ['id', 'Teams', 'Creativity av adj', 'Matches']

        for j in range(lastGW,0,-1):
            TeamCreativityAd['Creativity GW'+str(j)+' adj'] = [[] for _ in range(team_number)]
            for i in range(team_number):
                for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                    if toint(Fixtures[Fixtures['id']==Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==i+1:
                        TeamCreativityAd.at[i,'Creativity GW'+str(j)+' adj'].append(                            TeamCreativity.at[i,'Creativity GW'+str(j)][k]*                            threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Team_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                    else:
                          TeamCreativityAd.at[i,'Creativity GW'+str(j)+' adj'].append(                            TeamCreativity.at[i,'Creativity GW'+str(j)][k]*                            threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                    TeamCreativityAd.at[i,'Creativity av adj'] = TeamCreativityAd.at[i,'Creativity av adj']  +                         TeamCreativityAd.at[i,'Creativity GW'+str(j)+' adj'][k]


        TeamCreativityAd['Creativity av adj'] = TeamCreativityAd['Creativity av adj']/noZ(Teams['Matches'])
        
        print('4.5. TeamCreativityAd is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()
        
        #(6). Creating  a table with average threat allowed adjusted by teams and GW threat allowed adjusted

        TableDefenceAd = Teams.copy()
        TableDefenceAd.columns = ['id', 'Teams', 'Threat allowed av adj', 'Matches']

        for j in range(lastGW,0,-1):
            TableDefenceAd['Threat allowed GW'+str(j)+' adj'] = [[] for _ in range(team_number)]
            for i in range(team_number):
                for k in range(len(Team_fixtures.at[i, 'GW'+str(j)])):
                    if toint(Fixtures[Fixtures['id']==Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==i+1:
                        TableDefenceAd.at[i,'Threat allowed GW'+str(j)+' adj'].append(                            TableDefence.at[i,'Threat allowed GW'+str(j)][k]*                            threatAllowedAv/TeamThreat.at[toint(Fixtures[Fixtures['id']==                            Team_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat av'])
                    else:
                        TableDefenceAd.at[i,'Threat allowed GW'+str(j)+' adj'].append(                            TableDefence.at[i,'Threat allowed GW'+str(j)][k]*                            threatAllowedAv/TeamThreat.at[toint(Fixtures[Fixtures['id']==                            Team_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat av'])

                    TableDefenceAd.at[i,'Threat allowed av adj'] = TableDefenceAd.at[i,'Threat allowed av adj']  +                         TableDefenceAd.at[i,'Threat allowed GW'+str(j)+' adj'][k]


        TableDefenceAd['Threat allowed av adj'] = TableDefenceAd['Threat allowed av adj']/noZ(Teams['Matches'])

        print('4.6. TeamDefenceAd is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()


        #(7) Total Team Table

        TableTeams = pd.DataFrame()
        TableTeams['id'] = Teams['id']
        TableTeams['Team'] = Teams['Teams']

        TableTeams['Threat adjusted'] = TeamThreatAd['Threat av adj']
        TableTeams['Threat'] = TeamThreat['Threat av']
        TableTeams['Creativity adjusted'] = TeamCreativityAd['Creativity av adj']
        TableTeams['Creativity'] = TeamCreativity['Creativity av']
        TableTeams['Threat allowed adjusted'] = TableDefenceAd['Threat allowed av adj']
        TableTeams['Threat allowed'] = TableDefence['Threat allowed av']
        
        print('4.7. TableTeams is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

# 5. Calculating pLayer tables


        #(1) Players Threat

        PlayerThreat = Players.copy()
        PlayerThreat['Threat per fixture'] = np.zeros(len(Players))
        PlayerThreat['Threat per game'] = np.zeros(len(Players))

        for j in range(lastGW,0,-1):
            PlayerThreat['Threat GW'+str(j)] = [[] for _ in range(len(Players))]
            for i in range(len(Players)):
                for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):
                    PlayerThreat.at[i,'Threat GW'+str(j)].append(Table[(Table['fixture']==                        Player_fixtures.at[i, 'GW'+str(j)][k])&(Table['element']==                        PlayerThreat.at[i,'id'])]['threat'].sum())
                    PlayerThreat.at[i,'Threat per game'] = PlayerThreat.at[i,'Threat per game'] +                        PlayerThreat.at[i,'Threat GW'+str(j)][k]


        PlayerThreat['Threat per fixture'] = PlayerThreat['Threat per game']/noZ(Players['Team games'])
        PlayerThreat['Threat per game'] = PlayerThreat['Threat per game']/noZ(Players['Played'])
        
        print('5.1. PlayerThreat is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()
        
        #(2) Players Creativity

        PlayerCreativity = Players.copy()
        PlayerCreativity['Creativity per fixture'] = np.zeros(len(Players))
        PlayerCreativity['Creativity per game'] = np.zeros(len(Players))

        for j in range(lastGW,0,-1):
            PlayerCreativity['Creativity GW'+str(j)] = [[] for _ in range(len(Players))]
            for i in range(len(Players)):
                for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):
                    PlayerCreativity.at[i,'Creativity GW'+str(j)].append(Table[(Table['fixture']==                                                Player_fixtures.at[i, 'GW'+str(j)][k])&                                                (Table['element']==PlayerCreativity.at[i,'id'])]['creativity'].sum())
                    PlayerCreativity.at[i,'Creativity per game'] = PlayerCreativity.at[i,'Creativity per game'] +                        PlayerCreativity.at[i,'Creativity GW'+str(j)][k]


        PlayerCreativity['Creativity per fixture'] = PlayerCreativity['Creativity per game']/noZ(Players['Team games'])
        PlayerCreativity['Creativity per game'] = PlayerCreativity['Creativity per game']/noZ(Players['Played'])
        
        print('5.2. PlayerCreativity is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()
        
        #(3) Players Threat Adjusted

        PlayerThreatAd = Players.copy()
        PlayerThreatAd['Threat per fixture adj'] = np.zeros(len(Players))
        PlayerThreatAd['Threat per game adj'] = np.zeros(len(Players))

        for j in range(lastGW,0,-1):
            PlayerThreatAd['Threat GW'+str(j) + 'adj'] = [[] for _ in range(len(Players))]
            for i in range(len(Players)):
                for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):
                    #If player's team is away
                    if toint(Fixtures[Fixtures['id']==Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==                        PlayerThreatAd.at[i,'Team number']:
                        PlayerThreatAd.at[i,'Threat GW'+str(j) + 'adj'].append(PlayerThreat.at[i,'Threat GW'+str(j)][k]                            *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Player_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                    #If home
                    else:
                          PlayerThreatAd.at[i,'Threat GW'+str(j) + 'adj'].append(PlayerThreat.at[i,'Threat GW'+str(j)][k]
                            *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==\
                            Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                    PlayerThreatAd.at[i,'Threat per game adj'] = PlayerThreatAd.at[i,'Threat per game adj'] +                        PlayerThreatAd.at[i,'Threat GW'+str(j) + 'adj'][k]


        PlayerThreatAd['Threat per fixture adj'] = PlayerThreatAd['Threat per game adj']/noZ(Players['Team games'])
        PlayerThreatAd['Threat per game adj'] = PlayerThreatAd['Threat per game adj']/noZ(Players['Played'])

        print('5.3. PlayerThreatAd is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

        #(4) PLayers Creativity Adjusted

        PlayerCreativityAd = Players.copy()
        PlayerCreativityAd['Creativity per fixture adj'] = np.zeros(len(Players))
        PlayerCreativityAd['Creativity per game adj'] = np.zeros(len(Players))

        for j in range(lastGW,0,-1):
            PlayerCreativityAd['Creativity GW'+str(j) + 'adj'] = [[] for _ in Players.itertuples()]
            for i in range(len(Players)):
                for k in range(len(Player_fixtures.at[i, 'GW'+str(j)])):

                    if toint(Fixtures[Fixtures['id']==Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum())==                        PlayerCreativityAd.at[i,'Team number']:
                        PlayerCreativityAd.at[i,'Creativity GW'+str(j) + 'adj'].append(                            PlayerCreativity.at[i,'Creativity GW'+str(j)][k]                            *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Player_fixtures.at[i, 'GW'+str(j)][k]]['team_h'].sum()-1),'Threat allowed av'])
                    else:
                        PlayerCreativityAd.at[i,'Creativity GW'+str(j) + 'adj'].append(                            PlayerCreativity.at[i,'Creativity GW'+str(j)][k]                            *threatAllowedAv/TableDefence.at[toint(Fixtures[Fixtures['id']==                            Player_fixtures.at[i, 'GW'+str(j)][k]]['team_a'].sum()-1),'Threat allowed av'])

                    PlayerCreativityAd.at[i,'Creativity per game adj'] =                         PlayerCreativityAd.at[i,'Creativity per game adj'] +                        PlayerCreativityAd.at[i,'Creativity GW'+str(j) + 'adj'][k]


        PlayerCreativityAd['Creativity per fixture adj'] = PlayerCreativityAd['Creativity per game adj']/            noZ(Players['Team games'])
        PlayerCreativityAd['Creativity per game adj'] = PlayerCreativityAd['Creativity per game adj']/            noZ(Players['Played'])
        
        print('5.4. PlayerCreativityAd is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

# 6. Writing tables to files
        
        self.TeamThreat, self.TeamThreat_MA =            write_table(TeamThreat, 'TeamThreat', 'Threat av', self.source, self.ma_num)
        self.TeamCreativity, self.Creativity_MA = (write_table
            (TeamCreativity, 'TeamCreativity', 'Creativity av', self.source, self.ma_num))
        self.TableDefence, self.TableDefence_MA =            write_table(TableDefence, 'TableDefence', 'Threat allowed av', self.source, self.ma_num)
        self.TeamThreatAd, self.TeamThreatAd_MA =            write_table(TeamThreatAd, 'TeamThreatAd', 'Threat av adj', self.source, self.ma_num)
        self.TeamCreativityAd, self.CreativityAd_MA =            write_table(TeamCreativityAd, 'TeamCreativityAd', 'Creativity av adj', self.source, self.ma_num)
        self.TableDefenceAd, self.TableDefenceAd_MA =            write_table(TableDefenceAd, 'TableDefenceAd', 'Threat allowed av adj', self.source, self.ma_num)
        self.TableTeams, self.TableTeams_MA =            write_table(TableTeams, 'TableTeams', 'Threat adjusted', self.source, self.ma_num)
        
        self.PlayerThreat, self.PlayerThreat_MA =            write_table(PlayerThreat, 'PlayerThreat', 'Threat per fixture', self.source, self.ma_num)
        self.PlayerCreativity, self.PlayerCreativity_MA =            write_table(PlayerCreativity, 'PlayerCreativity', 'Creativity per fixture', self.source, self.ma_num)
        self.PlayerThreatAd, self.PlayerThreatAd_MA =            write_table(PlayerThreatAd, 'PlayerThreatAd', 'Threat per fixture adj', self.source, self.ma_num)
        self.PlayerCreativityAd, self.PlayerCreativityAd_MA =            write_table(PlayerCreativityAd, 'PlayerCreativityAd', 'Creativity per fixture adj', self.source, self.ma_num)
        
        self.Table = Table
        self.Fixtures = Fixtures
        self.Teams = Teams
        self.Players = Players
        
        print('6. Writing to files is over.\t It takes ' + str(time.time() - start) + ' sec')
        start = time.time()

# 7. Tests for each element of the class

    def test2FPL(self):
        FPL = pd.read_csv('in/Table_FPL.csv')
        Table_Source = pd.read_csv('in/Table_'+self.source+'.csv')
        #element_set = set(FPL['element'])
        Mistakes = pd.DataFrame()
        No_Names = pd.DataFrame()
        if self.source == 'FPL':
            return Mistakes, No_Names
        for i in Table_Source.index:
            if Table_Source.at[i,'element'] < 1000000:
                #print('!')
                FPLmin = FPL[(FPL['element'] == Table_Source.at[i,'element'])&                            (FPL['fixture'] == Table_Source.at[i,'fixture'])]['minutes'].sum()
                if abs(Table_Source.at[i,'minutes'] - FPLmin) > 10:
                    Mistakes = Mistakes.append(pd.DataFrame([[Table_Source.at[i,'player'], Table_Source.at[i,'element'],                        Table_Source.at[i,'fixture'], Table_Source.at[i,'minutes'], FPLmin]], columns = ['player',                        'element', 'fixture', 'minutes', 'FPL_minutes']), ignore_index=True)
            else:
                 No_Names = No_Names.append(pd.DataFrame([[Table_Source.at[i,'player'], Table_Source.at[i,'fixture']]],                    columns = ['player', 'fixture']), ignore_index=True)
        display(Mistakes)
        display(No_Names)
        return Mistakes, No_Names
        
    def test(self):
        start = time.time()
        
        constti.DRDC(self.TeamThreat)
        constti.DRDC(self.TeamCreativity)
        constti.DRDC(self.TeamThreatAd)
        constti.DRDC(self.TeamCreativityAd)
        constti.DRDC(self.TableTeams)
        constti.DRDC(self.PlayerThreat)
        constti.DRDC(self.PlayerCreativity)
        constti.DRDC(self.PlayerThreatAd)
        constti.DRDC(self.PlayerCreativityAd)
        
        self.test2FPL()
        
        print(self.source + '.test passed.')
        print('7. Testing is over.\t It takes ' + str(time.time() - start) + ' sec')

# 8. Useful not class functions
        
# Writing final tables to files and returning table itself and MA variant also
# df - Table to make final table out of it, name - the name of the table, key_col - column to sort,
# source - Understat o FPL, ma_num - number for MA
def write_table(df, name, key_col, source, ma_num):
    del df['id']
    if 'Team number' in df.columns:
        del df['Team number']
    df.sort_values(key_col, ascending = False, inplace = True)
    df.index = np.arange(1, len(df) + 1)
    df = Brr_functions.no_lists(df)
    df_ma = MA(df, ma_num)
    df_ma.to_csv(Path('out/' + source + '/' + name + '.csv'))
    return df, df_ma
        
def d_av(T, j, GW_columns, d):
    T[GW_columns[j] +' '+ str(d) + ' - average'] = [0.0 for i in T.itertuples()]
    for i in T.index:
        u = 0
        k = 0
        while (u < d)&(j-k>=0):
            if T.at[i, GW_columns[j-k]] != '':
                T.at[i, GW_columns[j] +' '+ str(d) + ' - average'] += T.at[i, GW_columns[j-k]]
                u+=1
                k+=1
            else: k+=1
        if u==d:
            T.at[i, GW_columns[j] +' '+ str(d) + ' - average'] = T.at[i, GW_columns[j] +' '+ str(d) + ' - average']/d
        else:
            T.loc[i, GW_columns[j] +' '+ str(d) + ' - average'] = ''
    return T[GW_columns[j] +' '+ str(d) + ' - average']
                    
def MA(Out_T, d):
    T = Out_T.copy()
    GW_columns = []
    gw_col=0
    for col in T.columns:
        if 'GW' in col:
            GW_columns.append(col)
            gw_col+=1
    GW_columns = [GW_columns[i] for i in range(len(GW_columns)-1, -1, -1)]
    #print(GW_columns)
    if d>gw_col:
        return T
    else:
        for j in range(gw_col-1, d-2, -1):
            #print(j)
            T[GW_columns[j] +' '+ str(d) + ' - average'] = d_av(T, j, GW_columns, d)#[0 for i in T.itertuples()]
    return T
        
if __name__ == '__main__':
    Understat = Source('Understat')
    Understat.test()
    display(MA(Understat.TeamThreatAd, 3))
    pass


# In[ ]:




