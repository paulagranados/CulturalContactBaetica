import re
import os
#text = ('dare.txt')
#found = re.findall ('html', text)
#text.split('html')
#	print (text)

with open("dare.txt", "r") as f:
    for l in f:
        found = re.findall("(.*)(\.html)")
        print(found)