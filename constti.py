#!/usr/bin/env python
# coding: utf-8

# In[2]:


def Doubles(a):
    ans = []
    for i in range(1,len(a)):
        if a[i] in a[:i]:
            ans.append(a[i])
    return ans
def DRDC(table):
    a = ['raws']
    a.extend(Doubles(table.index))
    a.append('columns')
    a.extend(Doubles(table.columns))
    return a

if __name__=="__main__":
    print('Hello')


# In[ ]:



