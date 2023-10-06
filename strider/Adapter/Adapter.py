from Adapter.DataFlowAdapter import DataFlowAdapter
from Adapter.AstAdapter import AstAdapter
from Adapter.Synthesis import Synthesis
from pyverilog.dataflow.dataflow import *
from pyverilog.vparser.ast import *

class Adapter:
    def __init__(self) -> None:
        self.patchFiles = []
        self.patchAsts = []

    def getPatchAst(self):
        return self.patchFiles, self.patchAsts
    
    def synthesize(self, instance, expectedValue, specifications, attributesDict, availableTerms, availableParameters, availabelRenameInfo, suspiciousBindDict, suspiciousNodes, allBindDicts):
        synthesis = Synthesis(instance, expectedValue, specifications, attributesDict, availableTerms, availableParameters, availabelRenameInfo)
        candidateBindDicts = synthesis.synthesize(suspiciousBindDict, suspiciousNodes, allBindDicts)
        posExpectedSignalValues = synthesis.getPosExpectedSignalValues()
        return candidateBindDicts, posExpectedSignalValues

    def adaptBindDict(self, bindDict, candidateBindDict):
        dfAdapter = DataFlowAdapter(bindDict, candidateBindDict)
        actions = dfAdapter.adapt()
        return actions

    def adaptAst(self, ast, dstTerms, parameterinfos, allActions, fileToModulesMap):
        astAdapter = AstAdapter(ast)
        self.patchFiles = []
        self.patchAsts = []
        for dstTerm, parameterinfo, actions in zip(dstTerms, parameterinfos, allActions):
            if actions == []: continue
            astAdapter.adapt(dstTerm, parameterinfo, actions, fileToModulesMap)
            patchFile, patchAst = astAdapter.getPatchAst()
            self.patchFiles.append(patchFile)
            self.patchAsts.append(patchAst)