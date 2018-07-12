import re
import os
#text = ('dare.txt')
#found = re.findall ('html', text)
#text.split('html')
#	print (text)

#with open("dare.txt", "r") as f:
#    for l in f:
#        found = re.match("(.*)(\.html)",l)
#        print(found)
        
with open("dare.txt", "r") as f:
    out = []
    for l in f:
        if l[-6:].rstrip() == ".html":
            out.append(l[:-6]+"\n")
        else:
            out.append(l)

test = open("dare-test.txt", "w")
for x in out:
    test.write(x)
test.close()  