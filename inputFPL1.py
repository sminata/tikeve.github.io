#!/usr/bin/env python
# coding: utf-8

# In[1]:


import constti
import Brr_functions
from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import numpy as np
from pathlib import Path
import unicodedata

#def inputFPL():
if 1:    
    url1 = "https://fantasy.premierleague.com/api/bootstrap-static/"
    url2 = "https://fantasy.premierleague.com/api/entry/698498/history/"
    url3 = "https://fantasy.premierleague.com/api/event/6/live/"
    url4 = "https://fantasy.premierleague.com/api/fixtures"
    url5 = 'https://fantasy.premierleague.com/api/element-summary/191/'
    
    #Kills unfinished matches
    def is_finished(n):
        if n=='':
            return False
        else:
            a = Fixtures[Fixtures['id']==n]['finished']
            return a.bool()
    
    p1 = constti.long_request(url1)  

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
    #bigTable.to_csv(Path('in/fpltable.csv'))
    
    teams = dict(zip(pd.DataFrame(d1['teams'])['id'],pd.DataFrame(d1['teams'])['name']))
    players = dict(zip(bigTable['id'],bigTable['full_name']))
    teamplayers = dict(zip(bigTable['id'],bigTable['team']))
    
    p4 = constti.long_request(url4) 
    d4 = json.loads(p4.text)
    Fixtures = pd.DataFrame(d4)
    #Fixtures.to_csv(Path('in/fplfixtures.csv'))
    
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


        
    
    Table = pd.DataFrame()
    for i in bigTable['id']:
        url = 'https://fantasy.premierleague.com/api/element-summary/'+str(i)+'/'
        p = constti.long_request(url)
        d = json.loads(p.text)
        dd = pd.DataFrame(d['history'])
        Table = Table.append(dd, ignore_index=True)
    #Table.to_csv(Path('in/TheTable.csv'))
    Table['threat'] = pd.to_numeric(Table['threat'])
    Table['creativity'] = pd.to_numeric(Table['creativity'])
    Table['team'] = [teamplayers[Table.at[i,'element']] for i in Table.index]

    
    
    
    
    Teams = pd.DataFrame()
    Teams['id'] = pd.DataFrame(d1['teams'])['id']
    Teams['Teams'] = pd.DataFrame(d1['teams'])['name']
    Teams['XXX Target number XXX'] = np.zeros(len(Teams))
    Teams['Matches'] = [len(Fixtures[Fixtures['finished']&((Fixtures['team_a']==i)|(Fixtures['team_h']==i))])                                   for i in range(1,len(Teams)+1)]


    Players = pd.DataFrame()
    Players['id'] = bigTable['id']
    Players['Name'] = constti.strip_accents_pdlist(pd.DataFrame(bigTable['full_name']))
    Players['web_name'] = constti.strip_accents_pdlist(pd.DataFrame(bigTable['web_name']))
    Players['Team number'] = [bigTable[bigTable['id'] == i]['team'].sum() for i in Players['id']]
    Players['Team'] = [dict(zip(pd.DataFrame(d1['teams'])['id'],pd.DataFrame(d1['teams'])['name']))                       [Players.at[i,'Team number']] for i in Players.index]
    Players['Team games'] = [Teams.at[Players.at[i,'Team number']-1,'Matches'] for i in Players.index]
    Players['Played'] = [len(Table[(Table['element']==i)&(Table['minutes']>0)])                             for i in Players['id']]

    
    
    
    
    Gameweeks = pd.DataFrame()
    for i in range(1,2*len(Teams) - 1):
        url = "https://fantasy.premierleague.com/api/event/" + str(i) + "/live/"
        p = constti.long_request(url) 
        d = json.loads(p.text)
        nexTour = pd.DataFrame(d['elements'])

        if not nexTour.empty:
            nt1 = pd.DataFrame(nexTour['stats'].tolist())
            nt1['id'] = nexTour['id']
            nt1['gameweek'] = i
            nt1['fixture'] = ''
            for j in nexTour.index:
                if len(nexTour.at[j,'explain'])==1:
                    nt1.at[j, 'fixture'] = nexTour.at[j,'explain'][0]['fixture']
                if len(nexTour.at[j,'explain'])==2:
                    nt1.at[j, 'fixture'] = nexTour.at[j,'explain'][1]['fixture']
                    newline = nt1.loc[j].copy()
                    newline['fixture'] = nexTour.at[j,'explain'][0]['fixture']
                    nt1 = nt1.append(newline, ignore_index=True)
                if len(nexTour.at[j,'explain'])==3:
                    nt1.at[j, 'fixture'] = nexTour.at[j,'explain'][2]['fixture']
                    newline1 = nt1.loc[j].copy()
                    newline2 = nt1.loc[j].copy()
                    newline1['fixture'] = nexTour.at[j,'explain'][1]['fixture']
                    newline2['fixture'] = nexTour.at[j,'explain'][0]['fixture']
                    nt1 = nt1.append(newline1, ignore_index=True)
                    nt1 = nt1.append(newline2, ignore_index=True)
                if len(nexTour.at[j,'explain'])>3:
                    print('Too many matches in Gameweek')
            Gameweeks = Gameweeks.append(nt1, ignore_index=True)
            print(i)

    Gameweeks['team'] = [teamplayers[i] for i in Gameweeks['id']]

    Gameweeks['threat'] = pd.to_numeric(Gameweeks['threat'])
    Gameweeks['creativity'] = pd.to_numeric(Gameweeks['creativity'])
    
    #Kill postponed matches lines

    li =[]
    for i in Gameweeks.index:
        if not is_finished(Gameweeks.at[i,'fixture']):
            li.append(i)
    Gameweeks = Gameweeks.drop(li)

    Gameweeks['team_a'] = [Fixtures[(pd.to_numeric(Fixtures['id']) == pd.to_numeric(Gameweeks.at[i,'fixture'])) &                                              ((Fixtures['team_a'] == Gameweeks.at[i,'team'])|                                              (Fixtures['team_h'] == Gameweeks.at[i,'team']))]['team_a'].values                                 for i in Gameweeks.index]

    Gameweeks['team_a'] = [int(Gameweeks.at[i,'team_a'][0]) if len(Gameweeks.at[i,'team_a'])==1 else '' for i in Gameweeks.index]

    Gameweeks['team_h'] = [Fixtures[(pd.to_numeric(Fixtures['id']) == pd.to_numeric(Gameweeks.at[i,'fixture'])) &                                              ((Fixtures['team_a'] == Gameweeks.at[i,'team'])|                                              (Fixtures['team_h'] == Gameweeks.at[i,'team']))]['team_h'].values                                 for i in Gameweeks.index]
    Gameweeks['team_h'] = [int(Gameweeks.at[i,'team_h'][0]) if len(Gameweeks.at[i,'team_h'])==1 else '' for i in Gameweeks.index]

    Gameweeks['teamAgainst'] = [Gameweeks.at[i,'team_a'] if Gameweeks.at[i,'team'] == Gameweeks.at[i,'team_h']                                else Gameweeks.at[i,'team_h']                                for i in Gameweeks.index]
    Gameweeks['side'] = ['home' if Gameweeks.at[i,'team'] == Gameweeks.at[i,'team_h']                                else 'away'                                for i in Gameweeks.index]

    del Gameweeks['team_a']
    del Gameweeks['team_h']
    

    Table.to_csv(Path('in/Table_FPL.csv'), index=False)
    Fixtures.to_csv(Path('in/Fixtures.csv'), index=False)
    Teams.to_csv(Path('in/Teams.csv'), index=False)
    Players.to_csv(Path('in/Players.csv'), index=False)
    Gameweeks.to_csv(Path('in/fplgameweeks.csv'), index=False)
    bigTable.to_csv(Path('in/fpltable.csv'), index=False)

    #return Table, Fixtures, Teams, Players

if __name__ == '__main__':
    Table, Fixtures, Teams, Players = inputFPL()
    display(Table)


# In[ ]:




