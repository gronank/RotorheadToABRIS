from serverreader import ServerReader
from condition import Condition, NameParser
from geometry import bufferZone, getPhaseLine, Color, NavPoint, Line, LineType, SymbolType
from exportabris import AbrisAdditional, AbrisNavigation
from parsecommands import ConsoleCommands
import json

def readFeatureSets(spec):
    reader = ServerReader(spec["serverUrl"])
    return {key:reader.readPoints(source) for key, source in spec["dataSources"].items()}

def getFeatures(spec, featureSets):
    condition = Condition(spec.get("condition"))
    return (ftr for setName in data["sources"] for ftr in featureSets[setName] if condition.match(ftr))

def parsePoints(pointSpecs, featureSets, disabler):
    points = []
    for pointSpec in pointSpecs:
        if disabler.disabled(pointSpec):
            continue
        symbolType = SymbolType.parse(pointSpec["symbolType"])
        nameParser = NameParser(pointSpec.get("name"))
        features = getFeatures(pointSpec, featureSets)
        for feature in features:
            nav=NavPoint()
            nav.point=feature.location
            nav.symbolType=symbolType
            nav.name = nameParser.parse(feature)
            points.append(nav)

    return points

def parseBufferZones(bufferSpecs, featureSets, disabler):
    zones = []
    for bufferSpec in bufferSpecs:
        if disabler.disabled(bufferSpec):
            continue
        units = getFeatures(bufferSpec, featureSets)
        friendlyBufferSize = bufferSpec["bufferSize"]#Nm
        style = LineType.parse(bufferSpec.get("style","line"))
        color = Color.parse(bufferSpec.get("color","black"))
        friendlyLocs=[ftr.location for ftr in units ]
        newZones = bufferZone(friendlyLocs, color, friendlyBufferSize)
        for zone in newZones:
            zone.type = style
        zones.append(newZones)
    return zones

def parseLines(lineSpecs, featureSets, disabler):
    lines = []
    for lineSpec in lineSpecs:
        if disabler.disabled(lineSpec):
            continue
        nameParser = NameParser(lineSpec.get("name"))
        color = Color.parse(lineSpec.get("color","black"))
        linePoints = {}
        pointFtrs = getFeatures(lineSpec, featureSets)
        for pointFtr in pointFtrs:
            pointName = nameParser.parse(pointFtr)
            linePoints.setdefault(pointName,[]).append(pointFtr.location)

        for name,pts in linePoints.items():
            linePts = getPhaseLine(pts)
            lines.append(Line(linePts,color,name))
    return lines

def exportToAbris(specPath, destinationFolder, disabler):
    with open(specPath,'r') as file:
        spec = json.load(file);
    featureSets = readFeatureSets(spec)

    navigation=AbrisNavigation()
    points = parsePoints(spec["points"], featureSets, disabler)
    navigation.AddNavPoints(points)
    navigation.Export(destinationFolder)

    additional = AbrisAdditional()
    bufferZones = parseBufferZones(spec["bufferZones"], featureSets, disabler)
    additional.AddLines(bufferZones)

    lines = parseLines(spec["lines"], featureSets, disabler);
    additional.AddLines(lines)

    additional.Export(destinationFolder);

if __name__=="__main__":
    consoleCommands = ConsoleCommands(sys.argv)
    exportToAbris(consoleCommands.specPath, consoleCommands.databasePath, consoleCommands.disabler)