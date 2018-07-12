import re

result = []

with open("dare.txt", "r") as f:
    filelines = f.readlines()
    
for fileLine in filelines:
    fileLine = fileLine.strip()
    lineElems = fileLine.split(",")
    
    for lineElem in lineElems:
        pattern = re.compile("(.*)\.html")
        if pattern.match(lineElem):
            #print("Adding %s" % lineElem)
            result.append(lineElem)
            
print(result)