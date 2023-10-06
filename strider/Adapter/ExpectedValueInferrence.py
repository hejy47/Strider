from pyverilog.dataflow.dataflow import *
from VerilogAnalyzer import SignalAnalyzer, DataFlowAnalyzer

def inferExpectedValue(spsNode, expectedValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo):
    # need to improve
    tmpExpectedValue = expectedValue
    if isinstance(expectedValue, bool):
        tmpExpectedValue = "'b1" if expectedValue == True else "'b0"
    elif isinstance(expectedValue, str):
        tmpExpectedValue = expectedValue.lower()
        if "'" not in tmpExpectedValue:
            tmpExpectedValue = bin(int(tmpExpectedValue)).replace("0b", "'b")
        elif "'d" in tmpExpectedValue:
            tmpExpectedValue = bin(int(tmpExpectedValue[tmpExpectedValue.index("'d")+2:])).replace("0b", "'b")
    # for DFTerminal
    if isinstance(spsNode, DFTerminal):
        if str(spsNode) not in possibleExpectedSignalValues:
            possibleExpectedSignalValues[str(spsNode)] = []
        if tmpExpectedValue not in possibleExpectedSignalValues[str(spsNode)]:
            possibleExpectedSignalValues[str(spsNode)].append(tmpExpectedValue)
    # for eq or neq and left/right is DFTerminal
    elif isinstance(spsNode, DFOperator):
        if spsNode.operator == "Eq" and expectedValue == True or spsNode.operator == "NotEq" and expectedValue == False:
            lValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.nextnodes[0])
            rValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.nextnodes[1])
            inferExpectedValue(spsNode.nextnodes[0], rValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            inferExpectedValue(spsNode.nextnodes[1], lValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        elif spsNode.operator == "Lor":
            inferExpectedValue(spsNode.nextnodes[0], tmpExpectedValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            inferExpectedValue(spsNode.nextnodes[1], tmpExpectedValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        elif spsNode.operator == "Land":
            inferExpectedValue(spsNode.nextnodes[0], tmpExpectedValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            inferExpectedValue(spsNode.nextnodes[1], tmpExpectedValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        elif spsNode.operator == "Plus":
            lValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.nextnodes[0])
            rValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.nextnodes[1])
            lVLen = len(lValue[lValue.index("'b")+2:]) if "'b" in lValue else len(bin(int(lValue))) - 2
            rVLen = len(rValue[rValue.index("'b")+2:]) if "'b" in rValue else len(bin(int(rValue))) - 2
            expectedLValue = SignalAnalyzer.converse(tmpExpectedValue) - SignalAnalyzer.converse(rValue)
            expectedRValue = SignalAnalyzer.converse(tmpExpectedValue) - SignalAnalyzer.converse(lValue)
            expectedLValue = "'b" + bin(abs(expectedLValue)).replace("0b", "")[-lVLen:].zfill(lVLen)
            expectedRValue = "'b" + bin(abs(expectedRValue)).replace("0b", "")[-rVLen:].zfill(rVLen)
            inferExpectedValue(spsNode.nextnodes[0], expectedLValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            inferExpectedValue(spsNode.nextnodes[0], expectedRValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        elif spsNode.operator == "Minus":
            lValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.nextnodes[0])
            rValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.nextnodes[1])
            lVLen = len(lValue[lValue.index("'b")+2:]) if "'b" in lValue else len(bin(int(lValue))) - 2
            rVLen = len(rValue[rValue.index("'b")+2:]) if "'b" in rValue else len(bin(int(rValue))) - 2
            expectedLValue = SignalAnalyzer.converse(tmpExpectedValue) + SignalAnalyzer.converse(rValue)
            expectedRValue = SignalAnalyzer.converse(lValue) - SignalAnalyzer.converse(tmpExpectedValue)
            expectedLValue = "'b" + bin(abs(expectedLValue)).replace("0b", "")[-lVLen:].zfill(lVLen)
            expectedRValue = "'b" + bin(abs(expectedRValue)).replace("0b", "")[-rVLen:].zfill(rVLen)
            inferExpectedValue(spsNode.nextnodes[0], expectedLValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            inferExpectedValue(spsNode.nextnodes[0], expectedRValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        elif spsNode.operator == "Ulnot":
            if SignalAnalyzer.equal(tmpExpectedValue, "'b0"):
                inferExpectedValue(spsNode.nextnodes[0], "'b1", possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            else:
                inferExpectedValue(spsNode.nextnodes[0], "'b0", possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
    elif isinstance(spsNode, DFPointer):
        vValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.var)
        ptr,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.ptr)
        ptr = SignalAnalyzer.converse(ptr)
        vLen = len(vValue[2:])
        # # enumerating is too much
        # expectedVarValue = ""
        # if ptr == 0:
        #     expectedVarValue = tmpExpectedValue[tmpExpectedValue.index("'b")+2:]
        #     if vLen-ptr > 1:
        #         for postV in range(2**(vLen-ptr)):
        #             tmpExpectedVarValue = bin(postV)[2:].zfill(vLen-ptr) + expectedVarValue
        #             inferExpectedValue(spsNode.var, "'b"+tmpExpectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        #     else:
        #         inferExpectedValue(spsNode.var, "'b"+expectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        # else:
        #     for prevV in range(2**ptr):
        #         expectedVarValue = tmpExpectedValue[tmpExpectedValue.index("'b")+2:] + bin(prevV)[2:].zfill(ptr)
        #         if vLen-ptr > 1:
        #             for postV in range(2**(vLen-ptr)):
        #                 tmpExpectedVarValue = bin(postV)[2:].zfill(vLen-ptr) + expectedVarValue
        #                 inferExpectedValue(spsNode.var, "'b"+tmpExpectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        #         else:
        #             inferExpectedValue(spsNode.var, "'b"+expectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        expectedVarValues = set(specifications.values()).union(set(parameters.values()))
        for expectedVarValue in expectedVarValues:
            if isinstance(expectedVarValue, str) and "'b" in expectedVarValue and len(expectedVarValue[expectedVarValue.index("'b")+2:]) == vLen:
                subExpectedValue = expectedVarValue[-ptr-1]
                if subExpectedValue == tmpExpectedValue[tmpExpectedValue.index("'b")+2:]:
                    inferExpectedValue(spsNode.var, expectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
    elif isinstance(spsNode, DFPartselect):
        vValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.var)
        lsb,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.lsb)
        msb,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, spsNode.msb)
        lsb,msb = SignalAnalyzer.converse(lsb), SignalAnalyzer.converse(msb)
        vLen = len(vValue[vValue.index("'b")+2:])
        # # enumerating is too much
        # expectedVarValue = ""
        # if lsb == 0:
        #     expectedVarValue = tmpExpectedValue[tmpExpectedValue.index("'b")+2:]
        #     if vLen-msb > 1:
        #         for postV in range(2**(vLen-msb)):
        #             tmpExpectedVarValue = bin(postV)[2:].zfill(vLen-msb) + expectedVarValue
        #             inferExpectedValue(spsNode.var, "'b"+tmpExpectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        #     else:
        #         inferExpectedValue(spsNode.var, "'b"+expectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        # else:
        #     for prevV in range(2**lsb):
        #         expectedVarValue = tmpExpectedValue[tmpExpectedValue.index("'b")+2:] + bin(prevV)[2:].zfill(lsb)
        #         if vLen-msb > 1:
        #             for postV in range(2**(vLen-msb)):
        #                 tmpExpectedVarValue = bin(postV)[2:].zfill(vLen-msb) + expectedVarValue
        #                 inferExpectedValue(spsNode.var, "'b"+tmpExpectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        #         else:
        #             inferExpectedValue(spsNode.var, "'b"+expectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
        expectedVarValues = set(specifications.values()).union(set(parameters.values()))
        for expectedVarValue in expectedVarValues:
            if isinstance(expectedVarValue, str) and "'b" in expectedVarValue and len(expectedVarValue[expectedVarValue.index("'b")+2:]) == vLen:
                subExpectedValue = expectedVarValue[-msb-1:-lsb] if lsb > 0 else expectedVarValue[-msb-1:]
                if subExpectedValue == tmpExpectedValue[tmpExpectedValue.index("'b")+2:]:
                    inferExpectedValue(spsNode.var, expectedVarValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
    elif isinstance(spsNode, DFConcat):
        index = 0
        for nextnode in spsNode.nextnodes:
            vValue,_ = DataFlowAnalyzer.traverseDataflow(instance, specifications, parameters, renameInfo, nextnode)
            vLen = len(vValue[2:])
            subExpectedValue = "'b" + tmpExpectedValue[tmpExpectedValue.index("'b")+2:][index:index+vLen]
            inferExpectedValue(nextnode, subExpectedValue, possibleExpectedSignalValues, instance, specifications, parameters, renameInfo)
            index += vLen