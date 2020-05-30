#!/usr/bin/env python
# coding: utf-8

# In[1]:


import unicodedata

# 1. Tries to download page 6 times instead of 1
def long_request(url):
    import requests
    for j in range(6):
        try:
            p = requests.get(url)
            return p
            #break
        except Exception as e:
            print(e)
    return CAN_NOT_CONNECT

# 2. Checks if list has the same elements
def Doubles(a):
    ans = []
    for i in range(1,len(a)):
        if a[i] in set(a[:i]):
            ans.append(a[i])
    return ans

# 3. Checks if a table has columns or rows with the same name.(That's a huge mistake!)
def DRDC(table):
    a = ['raws']
    a.extend(Doubles(table.index))
    a.append('columns')
    a.extend(Doubles(table.columns))
    return a

# 4. Delete accents above players names
def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

# 5. strip_accents for the 1st clumn of the table
# Need to be DataFrame,not a column constti.strip_accents_pdlist(pd.DataFrame(bigTable['web_name']))
def strip_accents_pdlist(a):
    b = a.copy()
    for i in range(len(a)):
        b.iat[i,0] = strip_accents(a.iat[i,0])
    return b

# 6. Changes name of a column col_name to new_col_name of a Table
def change_column_name(Table, col_name, new_col_name):
    if new_col_name in set(Table.columns):
        print("Can't change column name")
        return Table
    temp_Table = Table.copy()
    temp = temp_Table.columns
    temp = [temp[i] if temp[i] != col_name else new_col_name for i in range(len(temp))]
    temp_Table.columns = temp
    return temp_Table

# 7. Finds differences between the tables
def differences(A, B):
    df = (A == B)
    #df = Compare.copy()
    for i in df.index:
        if df.loc[i].sum() == len(df.columns):
            df = df.drop(i)
    for j in df.columns:
        if df[j].sum() == len(df):
            del df[j]
    return df

if __name__=="__main__":
    print('Hello')
    p = long_request('http://google.com')
    print(p.text)

