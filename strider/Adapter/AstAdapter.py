from pyverilog.vparser.ast import *
from pyverilog.dataflow.dataflow import *
from VerilogAnalyzer import AstAnalyzer

allClasses = globals()

class AstAdapter:
    def __init__(self, ast) -> None:
        self.ast = ast
        self.spsAstNode = None
        self.candidateAstNode = None
        self.parentSpsAstNode = None

        self.patchFile = None
        self.patchAst = None
    
    def getLRDelay(self, astNode, parameterinfo):
        ldelay, rdelay = None, None
        if parameterinfo == "nonblocking":
            substitutionType = NonblockingSubstitution
        elif parameterinfo == "blocking":
            substitutionType = BlockingSubstitution
        else:
            return ldelay, rdelay
        
        childrenAstNodes = [astNode]
        while len(childrenAstNodes) > 0:
            childAstNode = childrenAstNodes.pop(0)
            for cn in childAstNode.children():
                if isinstance(cn, substitutionType):
                    if cn.ldelay: ldelay = DelayStatement(cn.ldelay.delay)
                    if cn.rdelay: rdelay = DelayStatement(cn.rdelay.delay)
                    return ldelay, rdelay
                else:
                    childrenAstNodes.append(cn)
        return ldelay, rdelay

    def dfNodeToAstNode(self, dstTerm, parameterinfo, dfNode, actType=None):
        # dfNode is AstNode
        if isinstance(dfNode, Node): return dfNode
        astNode = None
        if isinstance(dfNode, DFTerminal):
            astNode = Identifier(dfNode.name.scopechain[-1].scopename)
        elif isinstance(dfNode, DFIntConst) or isinstance(dfNode, DFEvalValue):
            astNode = IntConst(dfNode.value)
        elif isinstance(dfNode, DFFloatConst):
            astNode = FloatConst(dfNode.value)
        elif isinstance(dfNode, DFStringConst):
            astNode = StringConst(dfNode.value)
        elif isinstance(dfNode, DFPartselect):
            astNode = Partselect(self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.var), self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.lsb), self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.msb))
        elif isinstance(dfNode, DFConcat):
            nextNodes = [self.dfNodeToAstNode(dstTerm, parameterinfo, n) for n in dfNode.nextnodes]
            astNode = Concat(tuple(nextNodes))
        elif isinstance(dfNode, DFOperator):
            op = dfNode.operator
            childrenNodes = [self.dfNodeToAstNode(dstTerm, parameterinfo, n) for n in dfNode.nextnodes]
            astNode = allClasses[op](*childrenNodes)
        
        ldelay, rdelay = self.getLRDelay(self.parentSpsAstNode, parameterinfo)
        if astNode:
            if self.spsAstNode == None and actType == "node":
                if parameterinfo == "nonblocking":
                    astNode = NonblockingSubstitution(Lvalue(Identifier(dstTerm)), Rvalue(astNode), ldelay, rdelay)
                elif parameterinfo == "blocking" or parameterinfo == None:
                    astNode = BlockingSubstitution(Lvalue(Identifier(dstTerm)), Rvalue(astNode), ldelay, rdelay)
            return astNode
        if isinstance(dfNode, DFBranch):
            trueStatement, falseStatement = None, None
            if isinstance(dfNode.truenode, DFBranch):
                trueStatement = self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.truenode)
            elif dfNode.truenode:
                if parameterinfo == "nonblocking":
                    trueStatement = NonblockingSubstitution(Lvalue(Identifier(dstTerm)), Rvalue(self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.truenode)), ldelay, rdelay)
                elif parameterinfo == "blocking" or parameterinfo == None:
                    trueStatement = BlockingSubstitution(Lvalue(Identifier(dstTerm)), Rvalue(self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.truenode)), ldelay, rdelay)
                elif parameterinfo == "assign":
                    trueStatement = self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.truenode)
            if isinstance(dfNode.falsenode, DFBranch):
                falseStatement = self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.falsenode)
            elif dfNode.falsenode:
                if parameterinfo == "nonblocking":
                    falseStatement = NonblockingSubstitution(Lvalue(Identifier(dstTerm)), Rvalue(self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.falsenode)), ldelay, rdelay)
                elif parameterinfo == "blocking" or parameterinfo == None:
                    falseStatement = BlockingSubstitution(Lvalue(Identifier(dstTerm)), Rvalue(self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.falsenode)), ldelay, rdelay)
                elif parameterinfo == "assign":
                    falseStatement = self.dfNodeToAstNode(dstTerm, parameterinfo, dfNode.falsenode)
            condNode = dfNode.condnode
            # the branch is case branch.
            parentParentSpsAstNode = self.getParentAstNode(self.parentSpsAstNode)
            if isinstance(parentParentSpsAstNode, CaseStatement):
                if isinstance(condNode, DFOperator) and condNode.operator == "Eq" and condNode.nextnodes[0].name.scopechain[-1].scopename == parentParentSpsAstNode.comp.name:
                    cond = self.dfNodeToAstNode(dstTerm, parameterinfo, condNode.nextnodes[1])
                    astNode = Case((cond,), trueStatement)
                    if isinstance(falseStatement, Case):
                        return [astNode, falseStatement]
                    elif isinstance(falseStatement, list) and len(falseStatement) > 0:
                        return [astNode].extend(falseStatement)
                    return astNode
            # the branch is assign branch
            if parameterinfo == "assign":
                cond = self.dfNodeToAstNode(dstTerm, parameterinfo, condNode)
                astNode = Cond(cond, trueStatement, falseStatement)
                return astNode
            # the branch is if else branch.
            cond = self.dfNodeToAstNode(dstTerm, parameterinfo, condNode)
            astNode = IfStatement(cond, trueStatement, falseStatement)
            return astNode
    
    def isChildAstNode(self, childNode, parentNode):
        if parentNode == childNode:
            return True
        for n in parentNode.children():
            if self.isChildAstNode(childNode, n):
                return True
        return False
    
    def getAstNode(self, nodeId):
        childrenAstNodes = [self.ast]
        while len(childrenAstNodes) > 0:
            childAstNode = childrenAstNodes.pop(0)
            if childAstNode.nodeid == nodeId:
                return childAstNode
            else:
                childrenAstNodes.extend(childAstNode.children())
    
    def getParentAstNode(self, astNode):
        childrenAstNodes = [self.ast]
        while len(childrenAstNodes) > 0:
            childAstNode = childrenAstNodes.pop(0)
            for cn in childAstNode.children():
                if cn == astNode:
                    return childAstNode
                childrenAstNodes.append(cn)
    
    def getSubCase(self, case, caseStament):
        assert isinstance(case, Case) and isinstance(caseStament, CaseStatement)
        for cs in caseStament.caselist:
            if case.cond == cs.cond:
                return cs
        return None
    
    def getSuperSubstitution(self, astNode, parentAstNode):
        childrenAstNodes = [parentAstNode]
        while len(childrenAstNodes) > 0:
            childAstNode = childrenAstNodes.pop(0)
            for cn in childAstNode.children():
                if isinstance(cn, Substitution):
                    if isinstance(cn.right, Rvalue) and cn.right.var == astNode:
                        return cn
                else:
                    childrenAstNodes.append(cn)
    
    def processBranchStatement(self, spsAstNode, candidateAstNode, parentSpsAstNode):
        nSpsAstNode, nCandidateAstNode, nParentSpsAstNode = spsAstNode, candidateAstNode, parentSpsAstNode
        if isinstance(parentSpsAstNode, Case):
            if isinstance(spsAstNode, Case) or isinstance(candidateAstNode, Case):
                nParentSpsAstNode = self.getParentAstNode(parentSpsAstNode)
                if spsAstNode == None:
                    subCase = self.getSubCase(candidateAstNode, nParentSpsAstNode)
                    # the case with same cond exists, update the statements.
                    if subCase:
                        nSpsAstNode = subCase
                        nCandidateStatement1 = candidateAstNode.statement
                        nCandidateStatement2 = subCase.statement
                        scope = None
                        if isinstance(nCandidateStatement1, Block):
                            nCandidateStatement1 = list(nCandidateStatement1.statements)
                        if isinstance(nCandidateStatement2, Block):
                            scope = nCandidateStatement2.scope
                            nCandidateStatement2 = list(nCandidateStatement2.statements)
                        if not isinstance(nCandidateStatement1, list):
                            nCandidateStatement1 = [nCandidateStatement1]
                        if not isinstance(nCandidateStatement2, list):
                            nCandidateStatement2 = [nCandidateStatement2]
                        nCandidateStatement = Block(nCandidateStatement1+nCandidateStatement2, scope)
                        nCandidateAstNode.statement = nCandidateStatement
                    # the case with same cond doesn't exists, insert the case.
                    else:
                        # nSpsAstNode = parentSpsAstNode
                        # nCandidateAstNode = [parentSpsAstNode, candidateAstNode]
                        nSpsAstNode = nParentSpsAstNode.caselist[-1]
                        if nSpsAstNode.cond == None: nSpsAstNode = nParentSpsAstNode.caselist[-2]
                        nCandidateAstNode = [nSpsAstNode, candidateAstNode]
            # insert/update default case.
            elif spsAstNode == None and isinstance(candidateAstNode, Substitution):
                nCandidateAstNode = Case(None, candidateAstNode)
                nSpsAstNode, nCandidateAstNode, nParentSpsAstNode = self.processBranchStatement(spsAstNode, nCandidateAstNode, parentSpsAstNode)
            elif spsAstNode != None and not self.isChildAstNode(spsAstNode, parentSpsAstNode):
                nParentSpsAstNode = self.getParentAstNode(spsAstNode)
        elif isinstance(parentSpsAstNode, IfStatement):
            if isinstance(candidateAstNode, IfStatement):
                # up the spsAstNode level to Substitution
                nSpsAstNode = self.getSuperSubstitution(spsAstNode, parentSpsAstNode)
            elif spsAstNode == None and isinstance(candidateAstNode, Substitution):
                for branch in [parentSpsAstNode.true_statement, parentSpsAstNode.false_statement]:
                    if isinstance(branch, Substitution):
                        if isinstance(branch.left.var, Identifier) and branch.left.var.name == candidateAstNode.left.var.name: continue
                        nSpsAstNode = branch
                        nCandidateAstNode = Block([branch, candidateAstNode])
                    elif isinstance(branch, Block):
                        nSpsAstNode = branch.statements[-1]
                        nCandidateAstNode = [branch.statements[-1], candidateAstNode]
                        for iStatement in branch.statements:
                            if isinstance(iStatement, Substitution):
                                if isinstance(iStatement.left.var, Identifier) and iStatement.left.var.name == candidateAstNode.left.var.name:
                                    nSpsAstNode, nCandidateAstNode = spsAstNode, candidateAstNode
                                    break
        return nSpsAstNode, nCandidateAstNode, nParentSpsAstNode

    def adapt(self, dstTerm, parameterinfo, actions, fileToModulesMap):
        parentModule = None
        for action in actions:
            spsDfNode, candidateDfNode, parentSpsDfNode, actType = action
            if parentSpsDfNode == None: self.parentSpsAstNode = self.ast
            else: self.parentSpsAstNode = self.getAstNode(parentSpsDfNode.nodeid)
            if self.parentSpsAstNode == None: continue
            if isinstance(spsDfNode, DFTerminal) and spsDfNode.name.scopechain[-1].scopename.startswith("_rn") and parameterinfo == "nonblocking":
                self.spsAstNode = self.getAstNode(candidateDfNode.nodeid)
                self.spsAstNode = self.getSuperSubstitution(self.spsAstNode, self.parentSpsAstNode)
                # if not isinstance(self.spsAstNode, BlockingSubstitution): import pdb; pdb.set_trace()
                assert isinstance(self.spsAstNode, BlockingSubstitution)
                self.candidateAstNode = NonblockingSubstitution(self.spsAstNode.left, self.spsAstNode.right, self.spsAstNode.ldelay, self.spsAstNode.rdelay)
            else:
                if spsDfNode: self.spsAstNode = self.getAstNode(spsDfNode.nodeid)
                self.candidateAstNode = self.dfNodeToAstNode(dstTerm[0].scopechain[-1].scopename, parameterinfo, candidateDfNode, actType)
                self.spsAstNode, self.candidateAstNode, self.parentSpsAstNode = self.processBranchStatement(self.spsAstNode, self.candidateAstNode, self.parentSpsAstNode)
                if self.parentSpsAstNode == self.spsAstNode: self.parentSpsAstNode = self.getParentAstNode(self.parentSpsAstNode)
            if parentModule == None:
                if self.spsAstNode:
                    parentModule = AstAnalyzer.getParentModule(self.ast, self.spsAstNode)
                else:
                    parentModule = AstAnalyzer.getParentModule(self.ast, self.parentSpsAstNode)
                # assert parentModule != None
                if parentModule == None: return
            self.replace(self.spsAstNode, self.candidateAstNode, self.parentSpsAstNode)
        self.patchFile, modules = AstAnalyzer.getSrcFileAndModules(parentModule, fileToModulesMap, self.ast)
        self.patchAst = Source("", Description(modules))
    
    def replace(self, node, newNode, parentNode):
        if node == newNode:
            return
        
        astNodes = [parentNode]
        while len(astNodes) > 0:
            astNode = astNodes.pop(0)
            if isinstance(astNode, Source):
                if astNode.description == node:
                    astNode.description = newNode
                    return
                astNodes.append(astNode.description)
            elif isinstance(astNode, Description):
                definitions = list(astNode.definitions)
                for i, n in enumerate(definitions):
                    if n == node:
                        if newNode == None:
                            definitions.pop(i)
                        elif isinstance(newNode, list):
                            newDefinitions = definitions[:i] + newNode + definitions[i+1:]
                            definitions = newDefinitions
                        else:
                            definitions[i] = newNode
                        astNode.definitions = tuple(definitions)
                        return
                astNodes.extend(astNode.definitions)
            elif isinstance(astNode, ModuleDef):
                if astNode.paramlist == node:
                    astNode.paramlist = newNode
                    return
                if astNode.portlist == node:
                    astNode.portlist = newNode
                    return
                items = list(astNode.items)
                for i, n in enumerate(items):
                    if n == node:
                        if newNode == None:
                            items.pop(i)
                        elif isinstance(newNode, list):
                            newItems = items[:i] + newNode + items[i+1:]
                            items = newItems
                        else:
                            items[i] = newNode
                        astNode.items = tuple(items)
                        return
                astNodes.extend([astNode.paramlist, astNode.portlist] + items)
            elif isinstance(astNode, Portlist):
                ports = list(astNode.ports)
                for i, n in enumerate(ports):
                    if n == node:
                        ports[i] = newNode
                        astNode.ports = tuple(ports)
                        return
                astNodes.extend(astNode.ports)
            elif isinstance(astNode, Ioport):
                if astNode.first == node:
                    astNode.first = newNode
                    return
                if astNode.second == node:
                    astNode.second = newNode
                    return
                astNodes.extend([astNode.first, astNode.second])
            elif isinstance(astNode, SensList):
                slist = list(astNode.list)
                for i, n in enumerate(slist):
                    if n == node:
                        if newNode == None:
                            slist.pop(i)
                        elif isinstance(newNode, list):
                            newSlist = slist[:i] + newNode + slist[i+1:]
                            slist = newSlist
                        else:
                            slist[i] = newNode
                        astNode.list = tuple(slist)
                        return
                astNodes.extend(slist)
            elif isinstance(astNode, Sens):
                if astNode.sig == node:
                    astNode.sig = newNode
                    return
                astNodes.append(astNode.sig)
            elif isinstance(astNode, Initial):
                if astNode.statement == node:
                    astNode.statement = newNode
                    return
                astNodes.append(astNode.statement)
            elif isinstance(astNode, Always):
                if astNode.sens_list == node:
                    astNode.sens_list = newNode
                    return
                if astNode.statement == node:
                    astNode.statement = newNode
                    return
                astNodes.extend([astNode.sens_list, astNode.statement])
            elif isinstance(astNode, Block):
                blockStatements = list(astNode.statements)
                for i, n in enumerate(blockStatements):
                    if n == node:
                        if newNode == None:
                            blockStatements.pop(i)
                        elif isinstance(newNode, list):
                            newBlockStatements = blockStatements[:i] + newNode + blockStatements[i+1:]
                            blockStatements = newBlockStatements
                        else:
                            blockStatements[i] = newNode
                        astNode.statements = tuple(blockStatements)
                        return
                astNodes.extend(astNode.statements)
            elif isinstance(astNode, IfStatement):
                if astNode.cond == node:
                    astNode.cond = newNode
                    return
                if astNode.true_statement == node:
                    astNode.true_statement = newNode
                    return
                if astNode.false_statement == node:
                    astNode.false_statement = newNode
                    return
                astNodes.extend([astNode.cond, astNode.true_statement, astNode.false_statement])
            elif isinstance(astNode, ForStatement):
                if astNode.pre == node:
                    astNode.pre = newNode
                    return
                if astNode.cond == node:
                    astNode.cond = newNode
                    return
                if astNode.post == node:
                    astNode.post = newNode
                    return
                if astNode.statement == node:
                    astNode.statement = newNode
                    return
                astNodes.extend([astNode.pre, astNode.cond, astNode.post, astNode.statement])
            elif isinstance(astNode, WhileStatement):
                if astNode.cond == node:
                    astNode.cond = newNode
                    return
                if astNode.statement == node:
                    astNode.statement = newNode
                    return
                astNodes.extend([astNode.cond, astNode.statement])
            elif isinstance(astNode, CaseStatement):
                if astNode.comp == node:
                    astNode.comp = newNode
                    return
                caseList = list(astNode.caselist)
                for i, n in enumerate(caseList):
                    if n == node:
                        if newNode == None:
                            caseList.pop(i)
                        elif isinstance(newNode, list):
                            newCaseList = caseList[:i] + newNode + caseList[i+1:]
                            caseList = newCaseList
                        else:
                            caseList[i] = newNode
                        astNode.caselist = tuple(caseList)
                        return
                astNodes.extend([astNode.comp] + caseList)
            elif isinstance(astNode, Case):
                condList = list(astNode.cond) if astNode.cond else []
                for i, n in enumerate(condList):
                    if n == node:
                        if newNode == None:
                            condList.pop(i)
                        elif isinstance(newNode, list):
                            newCondList = condList[:i] + newNode + condList[i+1:]
                            condList = newCondList
                        else:
                            condList[i] = newNode
                        astNode.cond = tuple(condList)
                        return
                if astNode.statement == node:
                    astNode.statement = newNode
                    return
                astNodes.extend(condList+[astNode.statement])
            elif isinstance(astNode, Assign) or isinstance(astNode, Substitution):
                if astNode.left == node:
                    astNode.left = newNode
                    return
                if astNode.right == node:
                    astNode.right = newNode
                    return
                if astNode.ldelay == node:
                    astNode.ldelay = newNode
                    return
                if astNode.rdelay == node:
                    astNode.rdelay = newNode
                    return
                astNodes.extend([astNode.left, astNode.right, astNode.ldelay, astNode.rdelay])
            elif isinstance(astNode, Lvalue) or isinstance(astNode, Rvalue):
                if astNode.var == node:
                    astNode.var = newNode
                    return
                astNodes.append(astNode.var)
            elif isinstance(astNode, UnaryOperator):
                if astNode.right == node:
                    astNode.right = newNode
                    return
                astNodes.append(astNode.right)
            elif isinstance(astNode, Cond):
                if astNode.cond == node:
                    astNode.cond = newNode
                    return
                if astNode.true_value == node:
                    astNode.true_value = newNode
                    return
                if astNode.false_value == node:
                    astNode.false_value = newNode
                    return
                astNodes.extend([astNode.cond, astNode.true_value, astNode.false_value])
            elif isinstance(astNode, Operator):
                if astNode.left == node:
                    astNode.left = newNode
                    return
                if astNode.right == node:
                    astNode.right = newNode
                    return
                astNodes.extend([astNode.left, astNode.right])
            elif isinstance(astNode, Identifier):
                if astNode.scope == node:
                    astNode.scope = newNode
                    return 
                astNodes.append(astNode.scope)
            elif isinstance(astNode, IdentifierScope):
                labelList = list(astNode.labellist)
                for i, n in enumerate(labelList):
                    if n == node:
                        if newNode == None:
                            labelList.pop(i)
                        else:
                            labelList[i] = newNode
                        astNode.labellist = tuple(labelList)
                        return
                astNodes.extend(labelList)

    def getPatchAst(self):
        return self.patchFile, self.patchAst