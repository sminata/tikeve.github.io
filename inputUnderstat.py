#!/usr/bin/env python
# coding: utf-8

# In[21]:


from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import numpy as np
import codecs
from pathlib import Path
import unicodedata
import constti

# 1.Check if there are equal names in the column
def  check_equal(Table, col_name): #Check doubles in column col_name of the table Table
    repetitions = pd.DataFrame()
    for i in range(len(Table)):
        if Table[col_name][i] in set(Table[col_name][:i]):
            if (len(repetitions)>0):
                if not (Table[col_name][i] in set(repetitions[col_name])):
                    repetitions = repetitions.append(Table[Table[col_name]==Table[col_name][i]])
            else:
                repetitions = repetitions.append(Table[Table[col_name]==Table[col_name][i]])
            #print('Check Equal', Table.iloc[i])
    print(repetitions)

# 2. Check if name_un is the same player as (name_fpl, web_name_fpl). Five comparison types: the lower the better         
def same_player(name_un, name_fpl, web_name_fpl, type_comp, repeat=1):
    name_un = name_un.lower()
    name_fpl = name_fpl.lower()
    web_name_fpl = web_name_fpl.lower()
    same = 0
    if (type_comp == 0)&(name_un == name_fpl): # Unerstat name = Full FPL name. Best equality
        same = 1
    
    if (type_comp == 1)&(web_name_fpl == name_un): # Understat name = Short FPL name.
        same = 1
        
    if (type_comp == 2)&(name_un in name_fpl): # Understat name is included in Full FPL name.
        same = 1

    if (type_comp == 3)&(set(name_un.split()) <= set(name_fpl.split())): # All words of Understat name are in Full FPL name
        same = 1

    if (type_comp == 4)&(web_name_fpl in name_un): # FPL Short name is included in Understat name
        same = 1

    if type_comp == 5: # Some ' ' space has been missed and after del of one space all words of Understat name are in Full FPL
        fpl_name = name_fpl.lower().split()
        for m in range(1,len(fpl_name)):
            if set(name_un.lower().split()) <=            set([fpl_name[k-1]+fpl_name[k] if k==m else ('' if k==m-1 else fpl_name[k])                 for k in range(0,len(fpl_name))]):
                    same = 1
    if (same == 0)&(repeat==1): # If '-' in Understat is ' ' in FPL
        return same_player(name_un.replace('-', ' '), name_fpl, web_name_fpl, type_comp, 0)
    return same

# 3. Adds match number game_number to Table and updates Dictionary of names
def add_match_to_dict(game_number, Dictionary):    
    
    url = 'https://understat.com/match/'+ str(game_number)
    #print(url)
    p = constti.long_request(url)
    pdecoded = codecs.decode(p.text,'unicode_escape')
    page = BeautifulSoup(p.text, 'html.parser')
    tempList = []
    for tags in page('script'):
        if '= JSON.parse' in str(tags):
            for els in str(tags).split():
                if 'JSON' in els:
                    els = els[12:-3]
                    els = codecs.decode(els,'unicode_escape')
                    tempList.append(json.loads(els))
    
    away_players = pd.DataFrame(tempList[2]['a']).transpose()
    home_players = pd.DataFrame(tempList[2]['h']).transpose()
    match_players = away_players.append(home_players)
    
    match_players['team_h_name'] = [teams_dict[tempList[1]['team_h']] for i in range(len(match_players))]
    match_players['team_a_name'] = [teams_dict[tempList[1]['team_a']] for i in range(len(match_players))]
    match_players['team_name'] = [match_players.at[i,'team_a_name'] if match_players.at[i,'h_a'] == 'a'                                            else match_players.at[i,'team_h_name'] for i in match_players.index]
    match_players['opponent_team_name'] = [match_players.at[i,'team_h_name'] if match_players.at[i,'h_a'] == 'a'                                            else match_players.at[i,'team_a_name'] for i in match_players.index]
    match_players['team_h'] = [dict(zip(Teams['Teams'], Teams['id']))[match_players.at[i,'team_h_name']]                                for i in match_players.index]
    match_players['team_a'] = [dict(zip(Teams['Teams'], Teams['id']))[match_players.at[i,'team_a_name']]                                for i in match_players.index]
    match_players['team'] = [dict(zip(Teams['Teams'], Teams['id']))[match_players.at[i,'team_name']]                            for i in match_players.index]
    match_players['opponent_team']=[dict(zip(Teams['Teams'], Teams['id']))[match_players.at[i,'opponent_team_name']]                       for i in match_players.index]
    match_players['fixture'] = [Fixtures[(Fixtures['team_a']==match_players['team_a'].mean())&                                     (Fixtures['team_h']==match_players['team_h'].mean())]['id'].sum()                                     for _ in match_players.index]
    match_players['round'] = [int(Fixtures[Fixtures['id']==match_players['fixture'].mean()]['event'].sum())                               for _ in match_players.index]
    match_players['player'] = constti.strip_accents_pdlist(pd.DataFrame(match_players['player']))
    
    
    FPL_names = constti.strip_accents_pdlist(pd.DataFrame([dict(zip(Players['id'], Players['Name']))                  [Table_FPL[Table_FPL['fixture']==match_players['fixture'].mean()].at[i,'element']]                    for i in Table_FPL[Table_FPL['fixture']==match_players['fixture'].mean()].index], columns = ['player']))
    FPL_names['web_name'] = constti.strip_accents_pdlist(pd.DataFrame([dict(zip(Players['id'], Players['web_name']))                  [Table_FPL[Table_FPL['fixture']==match_players['fixture'].mean()].at[i,'element']]                    for i in Table_FPL[Table_FPL['fixture']==match_players['fixture'].mean()].index]))

    FPL_names['id'] = [Table_FPL[Table_FPL['fixture']==match_players['fixture'].mean()].at[i,'element']                    for i in Table_FPL[Table_FPL['fixture']==match_players['fixture'].mean()].index]
    
    
    match_players['in_FPL'] = [0 for i in match_players.index]
    Dictionary_strong = Dictionary[Dictionary['id_fpl']!='']

    for i in match_players.index:
        match_players.at[i,'player'] = match_players.at[i,'player'].replace("&#039;", "'")#Чтобы правильно отображать апостроф
        if not(match_players.at[i,'player'] in set(Dictionary_strong['name_un'])):
            
            for t in range(6):
                for j in FPL_names.index:
                    if same_player(match_players.at[i,'player'], FPL_names.at[j,'player'], FPL_names.at[j,'web_name'], t):
                        match_players.at[i,'in_FPL'] = 1
                        name_un = match_players.at[i, 'player']
                        name_fpl = FPL_names.at[j,'player']
                        id_fpl = FPL_names.at[j,'id']
                        web_name_fpl = FPL_names.at[j,'web_name']
                        match_players.at[i, 'player'] = FPL_names.at[j,'player']
                        break
                if match_players.at[i,'in_FPL'] == 1:
                    break
            if match_players.at[i,'in_FPL'] == 0:
                name_un = match_players.at[i, 'player']
                name_fpl = ''
                id_fpl = ''
                web_name_fpl = ''
                
                
                
            if name_un in set(Dictionary['name_un']):
                print('SMTH went wrong')
                if name_fpl != '':
                    for u in Dictionary.index:
                        if name_un == Dictionary.at[u,'name_un']:
                            Dictionary.at[u,'name_fpl'] = name_fpl
                            Dictionary.at[u,'id_fpl'] = id_fpl
                            Dictionary.at[u,'web_name_fpl'] = web_name_fpl  
            else:

                Dictionary = Dictionary.append(pd.DataFrame(                    [[name_un, match_players.at[i, 'player_id'], name_fpl, id_fpl, web_name_fpl]],                    columns=["name_un", "id_un", 'name_fpl', 'id_fpl', 'web_name_fpl']), ignore_index=True)
        else:
            match_players.at[i, 'player'] = dict(zip(Dictionary['name_un'], Dictionary['name_fpl']))                [match_players.at[i, 'player']]
            match_players.at[i,'in_FPL'] = 1

    #print(FPL_names)                    
    return match_players, Dictionary

Table_FPL = pd.read_csv('in/Table_FPL.csv')
Fixtures = pd.read_csv('in/Fixtures.csv')
Teams = pd.read_csv('in/Teams.csv')
Players = pd.read_csv('in/Players.csv')

url = 'https://understat.com/match/11919'
url1 = 'https://understat.com/league/EPL'

p = constti.long_request(url1)
pdecoded = codecs.decode(p.text,'unicode_escape')
page = BeautifulSoup(p.text, 'html.parser')
a = []
for tags in page('script'):
    if '= JSON.parse' in str(tags):
        for els in str(tags).split():
            if 'JSON' in els:
                els = els[12:-3]
                els = codecs.decode(els,'unicode_escape')
                a.append(json.loads(els))
TT = pd.DataFrame(a[1]).transpose()
UnderstatTeams = dict(zip(TT['id'], TT['title']))
Schedule = pd.DataFrame(a[0])

#Словарь для перевода understat команд к FPL именам
teams_dtable = pd.DataFrame()
teams_dtable['understat'] = TT.sort_values(by=['title'])['title']
teams_dtable.index = np.arange(0, len(teams_dtable))
teams_dtable['fpl'] = Teams.sort_values(by=['Teams'])['Teams']
teams_dict = dict(zip(teams_dtable['understat'], teams_dtable['fpl']))


Table_Understat = pd.DataFrame()
Name_Dictionary = pd.DataFrame(columns=["name_un", "id_un", 'name_fpl', 'id_fpl', 'web_name_fpl'])
for i in range(len(Schedule)):
    if Schedule.at[i,'isResult']:
        MP, Name_Dictionary = add_match_to_dict(Schedule.at[i,'id'], Name_Dictionary)
        Table_Understat = Table_Understat.append(MP, ignore_index=True)

# Add fpl_id and name_fpl for players not in FPL
j=0
for i in Name_Dictionary.index:
    j+=1
    if Name_Dictionary.at[i,'name_fpl']=='':
        Name_Dictionary.at[i,'name_fpl'] = Name_Dictionary.at[i,'name_un']
        Name_Dictionary.at[i,'id_fpl'] = 1000000 + j
        
Table_Understat['element'] = [dict(zip(Name_Dictionary['name_fpl'], Name_Dictionary['id_fpl']))                              [Table_Understat.at[i, 'player']] for i in Table_Understat.index]
Table_Understat = constti.change_column_name(Table_Understat, 'xG', 'threat')
Table_Understat['threat']  = [100*float(Table_Understat['threat'][i]) for i in range(len(Table_Understat))]
Table_Understat = constti.change_column_name(Table_Understat, 'xA', 'creativity')
Table_Understat['creativity']  = [100*float(Table_Understat['creativity'][i]) for i in range(len(Table_Understat))]
Table_Understat = constti.change_column_name(Table_Understat, 'player_id', 'Understat_id')

Table_Understat.to_csv(Path('in/Table_Understat.csv'), index=False)
Name_Dictionary.to_csv(Path('in/Name_Dictionary.csv'), index=False)
Table_Understat


# In[ ]:




