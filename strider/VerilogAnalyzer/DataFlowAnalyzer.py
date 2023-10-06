import copy
import pyverilog
from pyverilog.dataflow.dataflow_analyzer import VerilogDataflowAnalyzer
from pyverilog.dataflow.optimizer import VerilogDataflowOptimizer
from pyverilog.dataflow.dataflow import *
from VerilogAnalyzer import SignalAnalyzer

class DataFlowAnalyzer:
    def __init__(self, args) -> None:
        self.analyzer = VerilogDataflowAnalyzer(args["filelist"], args["topmodule"],
                                       noreorder=args["noreorder"],
                                       nobind=args["nobind"],
                                       preprocess_include=args["include"],
                                       preprocess_define=args["define"])
        self.analyzer.generate()
        self.terms = self.analyzer.getTerms()
        self.bindDicts = self.analyzer.getBinddict()

        # self.optimizer = VerilogDataflowOptimizer(self.terms, self.bindDicts)
        # self.optimizer.resolveConstant()
        # self.resolvedTerms = self.optimizer.getResolvedTerms()
        # self.resolvedBindDict = self.optimizer.getResolvedBinddict()
        
        # Get the value of parameters.
        self.parameters = {}
        for k,v in self.terms.items():
            if "Parameter" in v.termtype or "Localparam" in v.termtype:
                pBindDict = self.bindDicts[k][0]
                pValue, _ = traverseDataflow("", {}, self.parameters, {}, pBindDict.tree)
                self.parameters[k] = pValue
    
    def getBindDicts(self):
        return self.bindDicts
    
    # def getDataflowNode(self, dfNode, nodeId):
    #     if dfNode.nodeid == nodeId:
    #         return dfNode
    #     for n in dfNode.children():
    #         childDfNode = self.getDataflowNode(n, nodeId)
    #         if childDfNode: return childDfNode

    #     return None
    
    def getTerms(self):
        return self.terms
    
    def getParameters(self):
        return self.parameters
    
def getBindDict(bindDicts, targetModule, targetSignal):
    for signal, bindDict in bindDicts.items():
        module, s = signal.scopechain[0].scopename, '.'.join([sc.scopename for sc in signal.scopechain[1:]])
        if module == targetModule and s == targetSignal:
            return bindDict
    return []

def traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree):
    dfEP = []
    if dfTree == None: return None, []
    dfEP.append(dfTree)
    # if dfTree.nodeid != None:
    #     dfEP.append(dfTree.nodeid)
    if isinstance(dfTree, DFBranch):
        cond, condEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.condnode)
        cond = SignalAnalyzer.converse(cond)
        if isinstance(cond, str) and ("x" in cond or "z" in cond):
            cond = False
        cond = bool(int(cond))
        if cond == True:
            trueV, trueEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.truenode)
            dfEP.extend(condEP+trueEP)
            return trueV, list(set(dfEP))
        if cond == False:
            falseV, falseEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.falsenode)
            dfEP.extend(condEP+falseEP)
            return falseV, list(set(dfEP))
    if isinstance(dfTree, DFOperator):
        if dfTree.operator == "Eq":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            if lValue == rValue:
                return 1, list(dfEP)
            else:
                return 0, list(dfEP)
        elif dfTree.operator == "NotEq":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            if lValue == rValue:
                return 0, list(dfEP)
            else:
                return 1, list(dfEP)
        elif dfTree.operator == "LessThan":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            if lValue < rValue:
                return 1, list(dfEP)
            else:
                return 0, list(dfEP)
        elif dfTree.operator == "GreaterThan":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            if lValue > rValue:
                return 1, list(dfEP)
            else:
                return 0, list(dfEP)
        elif dfTree.operator == "LessEq":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            if lValue <= rValue:
                return 1, list(dfEP)
            else:
                return 0, list(dfEP)
        elif dfTree.operator == "GreaterEq":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            if lValue >= rValue:
                return 1, list(dfEP)
            else:
                return 0, list(dfEP)
        elif dfTree.operator == "Plus":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue+rValue, list(dfEP)
        elif dfTree.operator == "Minus":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue-rValue, list(set(dfEP))
        elif dfTree.operator == "Times":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue*rValue, list(set(dfEP))
        elif dfTree.operator == "Divide":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue/rValue, list(set(dfEP))
        elif dfTree.operator == "Mod":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue%rValue, list(set(dfEP))
        elif dfTree.operator == "Power":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue**rValue, list(set(dfEP))
        elif dfTree.operator == "Land":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue and rValue, list(set(dfEP))
        elif dfTree.operator == "Lor":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return lValue or rValue, list(set(dfEP))
        elif dfTree.operator == "And":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return bin(lValue&rValue).replace("0b", "'b"), list(set(dfEP))
        elif dfTree.operator == "Or":
            lValue, lEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            rValue, rEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[1])
            dfEP.extend(lEP+rEP)

            lValue, rValue = SignalAnalyzer.converse(lValue), SignalAnalyzer.converse(rValue)
            if isinstance(lValue, str) and ("x" in lValue.lower() or "z" in lValue.lower()):
                return lValue, list(set(dfEP))
            if isinstance(rValue, str) and ("x" in rValue.lower() or "z" in rValue.lower()):
                return rValue, list(set(dfEP))
            return bin(lValue|rValue).replace("0b", "'b"), list(set(dfEP))
        elif dfTree.operator == "Unot":
            assert len(dfTree.nextnodes) == 1
            value, ep = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            dfEP.extend(ep)
            
            if isinstance(value, str):
                if "x" in value.lower() or "z" in value.lower():
                    return value, list(set(dfEP))
                vIndex = value.index("'b")+2 if "'b" in value else 0
                unotValue = value[:vIndex] + value[vIndex:].replace('0', '@').replace('1', '0').replace('@', '1')
            else:
                binValue = bin(value)
                unotValue = "'b" + binValue[2:].replace('0', '@').replace('1', '0').replace('@', '1')
            return unotValue, list(set(dfEP))
        elif dfTree.operator == "Ulnot":
            assert len(dfTree.nextnodes) == 1
            value, ep = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            dfEP.extend(ep)

            value = SignalAnalyzer.converse(value)
            if isinstance(value, str):
                return value, list(set(dfEP))
            ulnotValue = 1 if int(value) == 0 else 0
            return ulnotValue, list(set(dfEP))
        elif dfTree.operator == "Uor":
            assert len(dfTree.nextnodes) == 1
            value, ep = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.nextnodes[0])
            dfEP.extend(ep)
            
            uorValue = 0
            if isinstance(value, str):
                if "x" in value.lower() or "z" in value.lower():
                    return value, list(set(dfEP))
                vIndex = value.index("'b")+2 if "'b" in value else 0
                for value_i in value[vIndex:]:
                    uorValue = uorValue or int(value_i)
            else:
                binValue = bin(value)
                for value_i in binValue[2:]:
                    uorValue = uorValue or int(value_i)
            return uorValue, list(set(dfEP))
        # else:
        #     import pdb; pdb.set_trace()
    if isinstance(dfTree, DFConcat):
        concatValue = "'b"
        for n in dfTree.nextnodes:
            nv, nEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, n)
            if isinstance(nv, str) and "'b" in nv:
                nvb = nv[nv.index("'b")+2:]
                bitNum = int(nv[:nv.index("'b")]) if nv[:nv.index("'b")] != "" else 0
                concatValue += nvb.zfill(bitNum)
            elif isinstance(nv, str) and "'d" in nv:
                nvb = bin(int(nv[nv.index("'d")+2:]))[2:]
                bitNum = int(nv[:nv.index("'d")]) if nv[:nv.index("'d")] != "" else 0
                concatValue += nvb.zfill(bitNum)
            else:
                concatValue += bin(nv)[2:]
            dfEP.extend(nEP)
        return concatValue, list(set(dfEP))
    if isinstance(dfTree, DFTerminal):
        name = dfTree.name
        instanceSignal = "{}.{}".format(instance, name.scopechain[-1].scopename)
        supInstanceSignal = instanceSignal
        if "." in instance:
            supInstanceSignal = "{}.{}".format(instance[:instance.rindex(".")], name.scopechain[-1].scopename)
        if instanceSignal in tmpSignalValue:
            return tmpSignalValue[instanceSignal], dfEP
        elif supInstanceSignal in tmpSignalValue:
            return tmpSignalValue[supInstanceSignal], dfEP
        elif name in parameters:
            return parameters[name], dfEP
        elif name in renameInfo:
            return renameInfo[name], dfEP
        else:
            # raise ValueError("DFTerminal {} not in signal and parameter list.".format(str(name)))
            return "'bx", dfEP
    if isinstance(dfTree, DFConstant):
        return dfTree.value, dfEP
    if isinstance(dfTree, DFEvalValue):
        return dfTree.eval(), dfEP
    if isinstance(dfTree, DFPartselect):
        dfVar, varEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.var)
        lsbV, lsbEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.lsb)
        msbV, msbEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.msb)
        dfEP.extend(varEP+lsbEP+msbEP)
        
        if isinstance(dfVar, int):
            dfVar = bin(dfVar)[2:]
        dfVar = dfVar.replace("_", "")
        if "'b" in dfVar: dfVar = dfVar[dfVar.index("'b")+2:]
        lsbV, msbV = SignalAnalyzer.converse(lsbV), SignalAnalyzer.converse(msbV)
        retVar = dfVar[::-1][lsbV:msbV+1][::-1]
        if retVar == "": retVar = (msbV-lsbV+1) * '0'
        return "'b"+retVar, list(set(dfEP))
    if isinstance(dfTree, DFPointer):
        dfVar, varEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.var)
        ptrV, ptrEP = traverseDataflow(instance, tmpSignalValue, parameters, renameInfo, dfTree.ptr)
        dfEP.extend(varEP+ptrEP)

        if isinstance(dfVar, int):
            dfVar = bin(dfVar)[2:]
        dfVar = dfVar.replace("_", "")
        if "'b" in dfVar: dfVar = dfVar[dfVar.index("'b")+2:]
        ptrV = SignalAnalyzer.converse(ptrV)
        retVar = dfVar[::-1][ptrV] if ptrV < len(dfVar[::-1]) else "0"
        return "'b"+retVar, list(set(dfEP))
    return None, []

def copyDFNode(DFNode):
    retDFNode = copy.deepcopy(DFNode)
    retDFNode.nodeid = None
    children = list(retDFNode.children())
    for child in children:
        child.nodeid = None
        children.extend(child.children())
    return retDFNode

def equal(DFNode1, DFNode2):
    tmpDFNode1 = copyDFNode(DFNode1)
    tmpDFNode2 = copyDFNode(DFNode2)
    return tmpDFNode1 == tmpDFNode2

def getSuspiciousSignals(instance, sRenameInfo, executedPaths):
    suspiciousSignals = set()
    for ep in executedPaths:
        if isinstance(ep, DFTerminal):
            name = ep.name
            # filter rename signals
            if name in sRenameInfo: continue
            instanceSignal = "{}.{}".format(instance, name.scopechain[-1].scopename)
            suspiciousSignals.add(instanceSignal)
    return list(suspiciousSignals)