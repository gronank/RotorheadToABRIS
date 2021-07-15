import re
from serverreader import ServerReader
from geometry import bufferZone, getPhaseLine, Color, NavPoint, Line, LineType, SymbolType
from exportabris import AbrisAdditional, AbrisNavigation

def getSamName(unit):
	fullName=unit.description.split('Spotted: ')[1]
	name = fullName.split(' ')[0]
	return name
def getInfName(unit):
	c=re.match("Infantry <br>(\d+) Alive",unit.description).group(1)
	return c

def getVehcName(unit):
	name = unit.description.split(' ')[0]
	return name

def getObjName(unit):
	obj=re.match("Objective Area: (\w+).+",unit.description).group(1)
	return obj

def isPhaseLine(unit):
	return unit.description.startswith('PHASE LINE') or unit.description.startswith('PL')

url='http://rotorheads.ddns.net'
reader=ServerReader(url)
redForUrl='/mapdata/mapred.json'
unitsUrl='/mapdata/map.json'

# Visible units
navigation=AbrisNavigation()
units=reader.readPoints(unitsUrl)
navPoints = []
for unit in units:
	nav=NavPoint()
	if unit.description.startswith('Objective Area'):
		nav.symbolType=SymbolType.referencePoint
		nav.name=getObjName(unit)
		#nav.sub_type=8
	elif unit.icon=='sam':
		nav.symbolType=SymbolType.airDefenceHostile
		#nav.type_id=4
		nav.name=getSamName(unit)
		#nav.sub_type=2
	elif unit.icon=='infant':
		#nav.type_id=4
		#nav.sub_type=0
		nav.symbolType=SymbolType.unknownHostile
		nav.name=getInfName(unit)
	elif unit.icon=='bvehicle':
		#nav.type_id=0
		#nav.sub_type=1
		nav.symbolType=SymbolType.initialPoint
		nav.name=getVehcName(unit)
	else:
		continue
	nav.point=unit.location
	navPoints.append(nav)
navigation.AddNavPoints(navPoints)
navigation.Export()

# Danger zone
additionalInfo=AbrisAdditional()
redFtrs=reader.readPoints(redForUrl)
redPts=[ftr.location for ftr in redFtrs]
lines=bufferZone(redPts,Color.red)
for line in lines:
	line.type=LineType.filledHostile
additionalInfo.AddLines(lines)


# Phase lines
phaseLinePoints = {}

for ftr in units: 
	if isPhaseLine(ftr):
		name=ftr.description.split()[-1]
		phaseLinePoints.setdefault(name, []).append(ftr.location)

phaseLines = []
for name,pts in phaseLinePoints.items():
	linePts=getPhaseLine(pts)
	phaseLines.append(Line(linePts,Color.black,"PL "+name))

additionalInfo.AddLines(phaseLines)

additionalInfo.Export()
pass