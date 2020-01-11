#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

