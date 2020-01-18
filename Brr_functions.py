#!/usr/bin/env python
# coding: utf-8

# In[1]:


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

#removes lists from table adding new column instead
def no_lists(t):
    table = t.copy()
    for i in table.index:
        for j in table.columns:
            if type(table.at[i,j])==list:
                if len(table.at[i,j])==0:
                    table.at[i,j]=''
                elif len(table.at[i,j])==1:
                    table.at[i,j]=table.at[i,j][0]
                elif  len(table.at[i,j])==2:
                    if j+'*' not in table.columns:
                        table.insert(list(table.columns).index(j)+1,j+'*',''*len(table))
                    table.at[i,j+'*'] = table.at[i,j][1]
                    table.at[i,j]=table.at[i,j][0]
                else:#len(table.at[i,j])==3
                    if j+'*' not in table.columns:
                        table.insert(list(table.columns).index(j)+1,j+'*',''*len(table))
                    if j+'**' not in table.columns:
                        table.insert(list(table.columns).index(j)+2,j+'**',''*len(table))
                    table.at[i,j+'**'] = table.at[i,j][2]
                    table.at[i,j+'*'] = table.at[i,j][1]
                    table.at[i,j]=table.at[i,j][0]
    return table

