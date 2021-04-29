# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 19:07:17 2021

@author: Nithu
"""
import json
import random
import numpy as np
i = 0
parametercount = 30


setidx = []
paramname = []
val = []
datatype = []
while i < parametercount:
    i += 1
    j = random.randint(0,1)
    randomgenerator = random.randint(1,3)
    if randomgenerator == 1:
        k = np.float32(np.random.normal())
        l = str(k)
    if randomgenerator == 2:
        k = np.uint8(np.random.randint(0,1000))
        l = str(k)
    if randomgenerator == 3:
        k = np.int16(np.random.randint(-1000,1000))
        l = str(k)
    paramname.append(i)
    setidx.append(j)
    val.append(l)
    datatype.append(str(k.dtype))
    
inputdata = {'setidx':setidx,'pidx': paramname,'val':val,'dt':datatype}


with open('testdata.json','w') as f:
    json.dump(inputdata, f)

#with open('testdata.json', 'w') as f:
#   f.write(
#       '[' +
#       ',\n'.join(json.dumps(str(i)) for i in inputdata) +
#       ']\n')