
def processSignal(signalList):
    signalRecords = {}

    # processing headers
    headers = signalList[0].split(",")
    headers = [h.strip() for h in headers]

    for signalsStr in signalList[1:]:
        tSignals = signalsStr.split(",")
        tSignals = [ts.strip() for ts in tSignals]
        if len(tSignals) < len(headers):
            break
        for i, h in enumerate(headers):
            if h in signalRecords:
                signalRecords[h].append(tSignals[i])
            else:
                signalRecords[h] = [tSignals[i]]
    
    # aggregate signals
    uniqHeaders = set()
    uniqMaps = {}
    for h in headers:
        if "[" in h:
            uh = h[:h.index("[")]
            uniqHeaders.add(uh)
            if uh in uniqMaps:
                uniqMaps[uh].append(h)
            else:
                uniqMaps[uh] = [h]
        else:
            uniqHeaders.add(h)
    
    # sort signal list
    def takeIndex(elem):
        return int(elem[elem.index("[")+1:-1])
    for k, v in uniqMaps.items():
        v.sort(key=takeIndex, reverse=True)
    uniqSignalRecords = {}
    uniqHeaders = list(uniqHeaders)
    for uh in uniqHeaders:
        if signalRecords == {}:
            uniqSignalRecords[uh] = "'bx"
        elif uh in uniqMaps:
            uhSignals = [signalRecords[i] for i in uniqMaps[uh]]
            uhSignals = zip(*uhSignals)
            uhSignals = ["".join(uhs) for uhs in uhSignals]
            uniqSignalRecords[uh] = ["'b" + uhs for uhs in uhSignals]
        else:
            uniqSignalRecords[uh] = signalRecords[uh]
    return uniqSignalRecords

def getMismatchSignal(oracleOutput, simOutput):
    headers = list(oracleOutput.keys())
    sampleNum = len(oracleOutput[headers[0]])
    for i in range(sampleNum):
        mismatches = []
        for h in headers:
            if h not in simOutput:
                raise Exception("Inconsist signal.")
            else:
                oraVal = oracleOutput[h][i]
                simVal = simOutput[h][i]
                if oraVal != simVal:
                    mismatches.append(h)
        if mismatches != []:
            t = i
            if "time" in oracleOutput:
                t = oracleOutput["time"][i]
            return (t, mismatches)
    return (None, None)

def processOutputFile(oracleOutputPath, simOutputPath):
    oracleOutputList = open(oracleOutputPath, "r").readlines()
    simOutputList = open(simOutputPath, "r").readlines()
    oracleSignal = processSignal(oracleOutputList)
    simSignal = processSignal(simOutputList)
    return oracleSignal, simSignal

def equal(signalA, signalB):
    valueA, valueB = signalA, signalB
    if isinstance(signalA, str) and "'b" in signalA and ("x" not in signalA and "z" not in signalA):
        valueA = int(signalA[signalA.index("'b")+2:], 2)
    if isinstance(signalB, str) and "'b" in signalB and ("x" not in signalB and "z" not in signalB):
        valueB = int(signalB[signalB.index("'b")+2:], 2)
    return str(valueA) == str(valueB)

def converse(signal):
    if isinstance(signal, str):
        signal = signal.lower()
        if "x" in signal or "z" in signal:
            return signal
        elif "'b" in signal:
            return int(signal[signal.index("'b")+2:], 2)
        elif "'o" in signal:
            return int(signal[signal.index("'o")+2:], 8)
        elif "'d" in signal:
            return int(signal[signal.index("'d")+2:], 10)
        elif "'h" in signal:
            return int(signal[signal.index("'h")+2:], 16)
    elif isinstance(signal, float):
        return signal
    return int(signal)