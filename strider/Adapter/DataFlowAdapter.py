import copy
from pyverilog.dataflow.dataflow import *

class DataFlowAdapter:
    def __init__(self, bindDict, candidateBindDict) -> None:
        self.bindDict = bindDict
        self.candidateBindDict = candidateBindDict
    
    def adapt(self):
        assert self.candidateBindDict.dest == self.bindDict.dest
        actions =[]
        if self.candidateBindDict.alwaysinfo != self.bindDict.alwaysinfo:
            if self.candidateBindDict.alwaysinfo.clock != self.bindDict.alwaysinfo.clock:
                actions.append((self.bindDict.alwaysinfo.clock, self.candidateBindDict.alwaysinfo.clock, None, None))
            if self.candidateBindDict.alwaysinfo.reset != self.bindDict.alwaysinfo.reset:
                actions.append((self.bindDict.alwaysinfo.reset, self.candidateBindDict.alwaysinfo.reset, None, None))
            for sens1, sens2 in zip(self.bindDict.alwaysinfo.senslist, self.candidateBindDict.alwaysinfo.senslist):
                if sens1 != sens2:
                    actions.append((sens1, sens2, None, None))
        actions.extend(self.adaptDataflowNode(self.bindDict.tree, self.candidateBindDict.tree))
        return actions
    
    def adaptDataflowNode(self, dfNode, candidateDfNode, parentDfNode=None, actType="node"):
        if dfNode == candidateDfNode:
            return []
        else:
            if dfNode == None or candidateDfNode == None:
                return [(dfNode, candidateDfNode, parentDfNode, actType)]
            elif type(dfNode) != type(candidateDfNode):
                return [(dfNode, candidateDfNode, parentDfNode, actType)]
            elif isinstance(dfNode, DFConcat):
                acts = []
                parent = dfNode if dfNode.nodeid != None else parentDfNode
                sum1, sum2 = len(dfNode.nextnodes), len(candidateDfNode.nextnodes)
                for i in range(max(sum1, sum2)):
                    n1 = dfNode.nextnodes[i] if i < sum1 else None
                    n2 = candidateDfNode.nextnodes[i] if i < sum1 else None
                    acts.extend(self.adaptDataflowNode(n1, n2, parent, None))
                return acts
            elif isinstance(dfNode, DFOperator):
                if dfNode.operator != candidateDfNode.operator:
                    return [(dfNode, candidateDfNode, parentDfNode, actType)]
                acts = []
                parent = dfNode if dfNode.nodeid != None else parentDfNode
                for n1, n2 in zip(dfNode.nextnodes, candidateDfNode.nextnodes):
                    acts.extend(self.adaptDataflowNode(n1, n2, parent, None))
                return acts
            elif isinstance(dfNode, DFBranch):
                acts = []
                parent = dfNode if dfNode.nodeid != None else parentDfNode
                acts.extend(self.adaptDataflowNode(dfNode.condnode, candidateDfNode.condnode, parent, "edge"))
                acts.extend(self.adaptDataflowNode(dfNode.truenode, candidateDfNode.truenode, parent, "node"))
                acts.extend(self.adaptDataflowNode(dfNode.falsenode, candidateDfNode.falsenode, parent, "node"))
                return acts
            elif isinstance(dfNode, DFPartselect):
                acts = []
                parent = dfNode if dfNode.nodeid != None else parentDfNode
                acts.extend(self.adaptDataflowNode(dfNode.var, candidateDfNode.var, parent))
                acts.extend(self.adaptDataflowNode(dfNode.lsb, candidateDfNode.lsb, parent))
                acts.extend(self.adaptDataflowNode(dfNode.msb, candidateDfNode.msb, parent))
                return acts
            # elif isinstance(dfNode, DFTerminal) or isinstance(dfNode, DFConstant):
            #     return [(dfNode, candidateDfNode, parentDfNode)]
            else:
                return [(dfNode, candidateDfNode, parentDfNode, actType)]