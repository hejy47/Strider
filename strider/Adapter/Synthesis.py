import copy
from pyverilog.dataflow.dataflow import *
from VerilogAnalyzer import SignalAnalyzer, DataFlowAnalyzer
import Adapter.ExpectedValueInferrence as ExpectedValueInferrence

class Synthesis:
    def __init__(self, instance, expectedValue, specifications, attributesDict, terms, parameters, renameInfo) -> None:
        self.instance = instance
        self.expectedValue = expectedValue
        self.specifications = specifications
        self.attributesDict = attributesDict
        self.terms = terms
        self.parameters = parameters
        self.renameInfo = renameInfo
        self.spsConds = []
        self.spsNode = None
        self.posExpectedSignalValues = {}
    
    def synthesize(self, spsBindDict, spsNodes, allBindDicts):
        candidateBindDicts = []
        self.spsNode, self.spsConds = None, []
        self.collectSuspiciousNode(spsBindDict.tree, spsNodes)

        # for wire bug in module declaration, need to address
        if isinstance(self.spsNode, DFTerminal) and self.spsNode.name not in self.terms:
            return []

        # part select or point of expected value.
        lsb, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, spsBindDict.lsb)
        msb, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, spsBindDict.msb)
        if spsBindDict.ptr != None:
            ptr = []
            for ptri in spsBindDict.ptr:
                ptriValue, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, ptri)
                ptr.append(ptriValue)
            if len(ptr) == 1 and lsb == None and msb == None:
                ptr = int(ptr[0])
                expectedValue = self.expectedValue
                if "'b" in expectedValue: expectedValue = expectedValue[expectedValue.index("'b")+2:]
                expectedValue = expectedValue[::-1][ptr]
                self.expectedValue = "'b" + expectedValue
            # else:
            #     import pdb; pdb.set_trace()
        elif lsb != None and msb != None:
            lsb, msb = SignalAnalyzer.converse(lsb), SignalAnalyzer.converse(msb)
            expectedValue = self.expectedValue
            if "'b" in expectedValue: expectedValue = expectedValue[expectedValue.index("'b")+2:]
            expectedValue = expectedValue[::-1][lsb:msb+1][::-1]
            self.expectedValue = "'b" + expectedValue

        # lsb and msb of spsNode are generated when processing dfg
        lmsbEp = []
        if isinstance(self.spsNode, DFPartselect):
            _, spsNodeLsbEp = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, self.spsNode.lsb)
            _, spsNodeMsbEp = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, self.spsNode.msb)
            lmsbEp = [ep.nodeid for ep in spsNodeLsbEp+spsNodeMsbEp if ep.nodeid != None]

        # assume the assign node is faulty.
        candidateNodes = self.synthesizeNodes(lmsbEp)

        # collect the possible expected value of spsNode
        ExpectedValueInferrence.inferExpectedValue(self.spsNode, self.expectedValue, self.posExpectedSignalValues, \
            self.instance, self.specifications, self.parameters, self.renameInfo)

        # for the case of blocking subsitution
        if isinstance(self.spsNode, DFTerminal) and self.spsNode.name in self.renameInfo and spsBindDict.parameterinfo != "nonblocking" and spsBindDict.parameterinfo != "assign":
            renameNode = allBindDicts[self.spsNode.name][0].tree
            if isinstance(renameNode, DFTerminal): renameVar = renameNode.name
            elif isinstance(renameNode, DFPartselect): renameVar = renameNode.var.name
            else: renameNode, renameVar = None, None 
            while renameVar in self.renameInfo:
                renameNode = allBindDicts[renameVar][0].tree
                if isinstance(renameNode, DFTerminal): renameVar = renameNode.name
                elif isinstance(renameNode, DFPartselect): renameVar = renameNode.var.name
            # self.spsNode.nodeid = renameNode.nodeid
            if SignalAnalyzer.equal(DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, renameNode)[0], self.expectedValue):
                candidateBindDict = self.adapt(spsBindDict, spsBindDict.tree, self.spsNode, renameNode)
                candidateBindDict.parameterinfo = "nonblocking"
                candidateBindDicts.append(candidateBindDict)
        if spsBindDict.alwaysinfo != None:
            # always clock bug
            if spsBindDict.alwaysinfo.clock != None:
                if spsBindDict.alwaysinfo.clock_edge == "level":
                    for edge in ["posedge", "negedge"]:
                        candidateBindDict = copy.deepcopy(spsBindDict)
                        candidateBindDict.alwaysinfo.clock_edge = edge
                        candidateBindDict.alwaysinfo.clock.type = edge
                        candidateBindDicts.append(candidateBindDict)
                else:
                    edge = "posedge" if spsBindDict.alwaysinfo.clock_edge == "negedge" else "negedge"
                    candidateBindDict = copy.deepcopy(spsBindDict)
                    candidateBindDict.alwaysinfo.clock_edge = edge
                    candidateBindDict.alwaysinfo.clock.type = edge
                    candidateBindDicts.append(candidateBindDict)
            # always senslist
            if spsBindDict.alwaysinfo.senslist != []:
                for i,sens in enumerate(spsBindDict.alwaysinfo.senslist):
                    if sens.type == "posedge":
                        candidateBindDict = copy.deepcopy(spsBindDict)
                        candidateBindDict.alwaysinfo.senslist[i].type = "negedge"
                        candidateBindDicts.append(candidateBindDict)
                    elif sens.type == "negedge":
                        candidateBindDict = copy.deepcopy(spsBindDict)
                        candidateBindDict.alwaysinfo.senslist[i].type = "posedge"
                        candidateBindDicts.append(candidateBindDict)
        resortCandidateNodes = self.resortNodes(self.spsNode, candidateNodes)
        for candidateNode in resortCandidateNodes:
            candidateBindDict = self.adapt(spsBindDict, spsBindDict.tree, self.spsNode, candidateNode)
            candidateBindDicts.append(candidateBindDict)
        
        # assume the conds are faulty.
        candidateTrueEdges = self.synthesizeEdges(True)
        candidateFalseEdges = self.synthesizeEdges(False)
        expectedConds = self.getExpectedExecutedBranch(spsBindDict.tree, [])
        if len(expectedConds) == 0:
            # infer expected value
            for spsCond in self.spsConds:
                condValue, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, spsCond)
                condValue = str(condValue)
                condValue = condValue[condValue.index("'b")+2:] if "'b" in condValue else condValue
                if "x" in condValue or "z" in condValue: condValue = False
                condValue = bool(int(condValue))
                ExpectedValueInferrence.inferExpectedValue(spsCond, not condValue, self.posExpectedSignalValues, \
                                self.instance, self.specifications, self.parameters, self.renameInfo)
            
            # insert an extra branch
            candidateBranches = []
            for cte in candidateTrueEdges:
                for cn in candidateNodes:
                    if isinstance(self.spsNode, DFPartselect) and lmsbEp == []:
                        candidateBranch = DFBranch(cte, cn, copy.deepcopy(self.spsNode.var))
                    else:
                        candidateBranch = DFBranch(cte, cn, copy.deepcopy(self.spsNode))
                    candidateBranches.append(candidateBranch)
            for candidateBranch in candidateBranches:
                candidateBindDict = self.adapt(spsBindDict, spsBindDict.tree, self.spsNode, candidateBranch)
                candidateBindDicts.append(candidateBindDict)
        else:
            for expectedCond in expectedConds:
                tmpBindDicts = [spsBindDict]
                for (eCond, eValue) in expectedCond:
                    # # collect the possible expected value of spsCond
                    ExpectedValueInferrence.inferExpectedValue(eCond, eValue, self.posExpectedSignalValues, \
                                self.instance, self.specifications, self.parameters, self.renameInfo)

                    if eCond not in self.spsConds: continue
                    aValue,_ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, eCond)
                    if isinstance(aValue, str) and ('x' in aValue or 'z' in aValue):
                        # aValue = False
                        continue
                    elif isinstance(aValue, str):
                        aValue = SignalAnalyzer.converse(aValue)
                    if bool(int(aValue)) == eValue: continue

                    # systhesize candidate edges
                    candidateEdges = candidateTrueEdges if eValue else candidateFalseEdges
                    candidateEdges = self.resortEdges(eCond, candidateEdges)
                    tmpBindDicts2 = []
                    for tbd in tmpBindDicts:
                        for candidateEdge in candidateEdges:
                            # For case statement, the candidate edge should be eq and left should be consist.
                            if isinstance(eCond, DFOperator) and eCond.operator == "Eq" and eCond.nodeid == None:
                                if not (isinstance(candidateEdge, DFOperator) and candidateEdge.operator == "Eq" and DataFlowAnalyzer.equal(eCond.nextnodes[0], candidateEdge.nextnodes[0])):
                                    continue
                            candidateBindDict = self.adapt(tbd, tbd.tree, eCond, candidateEdge)
                            tmpBindDicts2.append(candidateBindDict)
                    tmpBindDicts = tmpBindDicts2
                candidateBindDicts.extend(tmpBindDicts)

        candidateBindDicts = list(filter(None, candidateBindDicts))
        
        return candidateBindDicts
    
    def adapt(self, spsBindDict, spsParentNode, spsNode, candidateNode):
        if isinstance(spsParentNode, DFBranch):
            if spsParentNode.condnode == spsNode:
                tmpNode = spsParentNode.condnode
                spsParentNode.condnode = candidateNode
                retBindDict = copy.deepcopy(spsBindDict)
                spsParentNode.condnode = tmpNode
                return retBindDict
            if spsParentNode.truenode == spsNode:
                tmpNode = spsParentNode.truenode
                spsParentNode.truenode = candidateNode
                retBindDict = copy.deepcopy(spsBindDict)
                spsParentNode.truenode = tmpNode
                return retBindDict
            if spsParentNode.falsenode == spsNode:
                tmpNode = spsParentNode.falsenode
                spsParentNode.falsenode = candidateNode
                retBindDict = copy.deepcopy(spsBindDict)
                spsParentNode.falsenode = tmpNode
                return retBindDict
            retBindDict = self.adapt(spsBindDict, spsParentNode.truenode, spsNode, candidateNode)
            if retBindDict: return retBindDict
            retBindDict = self.adapt(spsBindDict, spsParentNode.falsenode, spsNode, candidateNode)
            if retBindDict: return retBindDict
        elif spsBindDict.tree == spsNode:
            retBindDict = copy.deepcopy(spsBindDict)
            retBindDict.tree = candidateNode
            return retBindDict
    
    def collectSuspiciousNode(self, dfNode, nodes):
        if isinstance(dfNode, DFBranch):
            if dfNode.condnode in nodes:
                if dfNode.condnode not in self.spsConds:
                    self.spsConds.append(dfNode.condnode)
            if dfNode.truenode in nodes:
                if not isinstance(dfNode.truenode, DFBranch):
                    self.spsNode = dfNode.truenode
                else:
                    self.collectSuspiciousNode(dfNode.truenode, nodes)
            if dfNode.falsenode in nodes:
                if not isinstance(dfNode.falsenode, DFBranch):
                    self.spsNode = dfNode.falsenode
                else:
                    self.collectSuspiciousNode(dfNode.falsenode, nodes)
        else:
            self.spsNode = dfNode
    
    def getExpectedExecutedBranch(self, dfNode, branchConds=[]):
        if dfNode == None: return []
        retBranches = []
        if isinstance(dfNode, DFBranch):
            branch1 = self.getExpectedExecutedBranch(dfNode.truenode, branchConds+[(dfNode.condnode, True)])
            branch2 = self.getExpectedExecutedBranch(dfNode.falsenode, branchConds+[(dfNode.condnode, False)])
            for b in branch1:
                retBranches.append(b)
            for b in branch2:
                retBranches.append(b)
            return retBranches
        else:
            retValue, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, dfNode)
            if SignalAnalyzer.equal(retValue, self.expectedValue):
                return [branchConds]
            else:
                return []
    
    def getTerm(self, term):
        for k,v in self.terms.items():
            instanceSignal = "{}.{}".format(self.instance, k.scopechain[-1].scopename)
            if instanceSignal == term:
                return k, v
        return None, None
    
    def resortEdges(self, srcCond, candidateEdges):
        edges1, edges2 = [], []
        for candidateEdge in candidateEdges:
            if isinstance(candidateEdge, DFOperator) and candidateEdge.operator == "Eq":
                edges1.append(candidateEdge)
            else:
                edges2.append(candidateEdge)
        
        retEdges = []
        if isinstance(srcCond, DFOperator) and srcCond.operator == "Eq":
            eqEdges1, eqEdges2 = [], []
            for candidateEdge in edges1:
                if DataFlowAnalyzer.equal(srcCond.nextnodes[0], candidateEdge.nextnodes[0]):
                    eqEdges1.append(candidateEdge)
                else:
                    eqEdges2.append(candidateEdge)
            retEdges = eqEdges1 + eqEdges2 + edges2
        else:
            tEdges1, tEdges2 = [], []
            for candidateEdge in edges2:
                if isinstance(candidateEdge, DFOperator) and DataFlowAnalyzer.equal(candidateEdge.nextnodes[0], srcCond):
                    tEdges1.append(candidateEdge)
                else:
                    tEdges2.append(candidateEdge)
            retEdges = tEdges1 + tEdges2 + edges1
        return retEdges
    
    def synthesizeEdges(self, expectedCond):
        candidateEdges = []

        # synthesize from existing conditions
        for cond in self.spsConds:
            condValue, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, cond)
            condValue = str(condValue)
            condValue = condValue[condValue.index("'b")+2:] if "'b" in condValue else condValue
            if "x" in condValue or "z" in condValue: condValue = False
            if not isinstance(cond, DFOperator) or "Eq" not in cond.operator:
                if bool(int(condValue)) == expectedCond:
                    candidateEdges.append(DataFlowAnalyzer.copyDFNode(cond))
                else:
                    candidateEdges.append(DataFlowAnalyzer.copyDFNode(DFOperator([cond], "Ulnot")))
            if isinstance(cond, DFOperator):
                lValue, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, cond.nextnodes[0])
                if bool(int(condValue)) == expectedCond:
                    candidateEdges.append(DataFlowAnalyzer.copyDFNode(cond))
                if expectedCond:
                    cn = DFOperator([cond.nextnodes[0], DFIntConst(lValue)], "Eq")
                    candidateEdges.append(DataFlowAnalyzer.copyDFNode(cn))
                else:
                    cn = DFOperator([cond.nextnodes[0], DFIntConst(lValue)], "NotEq")
                    candidateEdges.append(DataFlowAnalyzer.copyDFNode(cn))
        
        # synthesize from specifications
        for term, value in self.specifications.items():
            if "clk" in term.lower() or "clock" in term.lower(): continue
            if self.instance not in term: continue
            sc, _ = self.getTerm(term)
            if sc == None: continue
            if 'x' in value or 'z' in value:
                pass
            else:
                boolValue = value[value.index("'b")+2:] if "'b" in value else value
                if bool(int(boolValue)) == expectedCond:
                    cn = DFTerminal(sc)
                    candidateEdges.append(cn)
                else:
                    if self.attributesDict[term]["size"] == 1:
                        cn = DFOperator([DFTerminal(sc)], "Unot")
                        candidateEdges.append(cn)
                    else:
                        cn = DFOperator([DFTerminal(sc)], "Ulnot")
                        candidateEdges.append(cn)
                
                if expectedCond:
                    cn = DFOperator([DFTerminal(sc), DFIntConst(value)], "Eq")
                    candidateEdges.append(cn)
                else:
                    cn = DFOperator([DFTerminal(sc), DFIntConst(value)], "NotEq")
                    candidateEdges.append(cn)
        uniCandidateEdges = list(set(candidateEdges))
        uniCandidateEdges.sort(key=candidateEdges.index)
        return uniCandidateEdges
    
    def resortNodes(self, spsNode, candidateNodes):
        retNodes1, retNodes2 = [], []
        for candidateNode in candidateNodes:
            if type(spsNode) == type(candidateNode):
                retNodes1.append(candidateNode)
            else:
                retNodes2.append(candidateNode)
        return retNodes1+retNodes2
    
    def synthesizeNodes(self, lmsbEp):
        candidateNodes = []
        if isinstance(self.spsNode, DFPartselect):
            lsb, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, self.spsNode.lsb)
            msb, _ = DataFlowAnalyzer.traverseDataflow(self.instance, self.specifications, self.parameters, self.renameInfo, self.spsNode.msb)
            lsb, msb = SignalAnalyzer.converse(lsb), SignalAnalyzer.converse(msb)
            var = self.spsNode.var
            if isinstance(var, DFIntConst):
                value = var.value.replace('_', '')
                if "'b" in value: value = value[value.index("'b")+2:]
                reverseValue = value[::-1]

                expectedValue = self.expectedValue
                if "'b" in expectedValue: expectedValue = expectedValue[expectedValue.index("'b")+2:]
                expectedValue = expectedValue[::-1]
                candidateValue = reverseValue[:lsb] + expectedValue + reverseValue[msb+1:]
                cn = copy.deepcopy(self.spsNode)
                cn.var.value = "'b" + candidateValue[::-1]
                if lmsbEp != []:
                    candidateNodes.append(cn)
                else:
                    candidateNodes.append(cn.var)
                    return candidateNodes
        elif isinstance(self.spsNode, DFPointer):
            # todo
            pass

        cn = DFIntConst(self.expectedValue)
        candidateNodes.append(cn)
        for term, value in self.specifications.items():
            if "clk" in term.lower() or "clock" in term.lower(): continue
            if self.instance not in term: continue
            if self.expectedValue == value:
                sc, _ = self.getTerm(term)
                if sc == None: continue
                cn = DFTerminal(sc)
                candidateNodes.append(cn)
        uniCandidateNodes = list(set(candidateNodes))
        uniCandidateNodes.sort(key=candidateNodes.index)
        return uniCandidateNodes

    def getPosExpectedSignalValues(self):
        return self.posExpectedSignalValues