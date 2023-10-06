import os
import pyverilog
from pyverilog.vparser.ast import *
from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

class AstParser:
    def __init__(self, args) -> None:
        self.ast, _ = parse(args["filelist"],
                        preprocess_include=args["include"],
                        preprocess_define=args["define"])

    def getAst(self):
        return self.ast

class AstGenerator:
    def __init__(self) -> None:
        self.generator = ASTCodeGenerator()
    
    def visit(self, ast):
        code = self.generator.visit(ast)
        return code
    
# def getModuleAndInstance(vast, currentModule=None):
#     modules = []
#     instances = {}
#     if isinstance(vast, ModuleDef):
#         modules.append(vast.name)
#         currentModule = vast.name
#     elif isinstance(vast, Instance):
#         if currentModule not in instances:
#             instances[currentModule] = []
#         instances[currentModule].append((vast.module, vast.name))
#     for childAst in vast.children():
#         childModules, childInstances = getModuleAndInstance(childAst, currentModule)
#         modules.extend(childModules)
#         for k,v in childInstances.items():
#             if k in instances:
#                 instances[k].extend(v)
#             else:
#                 instances[k] = v
#     return modules, instances

def getParentModule(parentAstNode, astNode, currentModule=None):
    if isinstance(parentAstNode, ModuleDef):
        currentModule = parentAstNode.name
    if parentAstNode == astNode:
        return currentModule
    for cn in parentAstNode.children():
        retModule = getParentModule(cn, astNode, currentModule)
        if retModule: return retModule
    return None

def getAllModules(vast):
    if isinstance(vast, ModuleDef):
        return [vast.name]
    allModules = []
    for childAst in vast.children():
        childModules = getAllModules(childAst)
        allModules.extend(childModules)
    return allModules

def getModuleDefAstNodes(sourceAst, moduleNames):
    retModules = []
    assert isinstance(sourceAst, Source)
    for module in sourceAst.description.definitions:
        assert isinstance(module, ModuleDef)
        if module.name in moduleNames:
            retModules.append(module)
    return tuple(retModules)

def mapFileToModule(args):
    fileToModulesMap = {}
    for srcFile in args["filelist"]:
        try:
            tmpArgs = {"filelist":[srcFile], "include":args["include"], "define":args["define"]}
            tmpAst = AstParser(tmpArgs).getAst()
            tmpModules = getAllModules(tmpAst)
            fileToModulesMap[srcFile] = tmpModules
        except Exception as e:
            pass
    return fileToModulesMap

def getSrcFileAndModules(module, fileToModulesMap, vast):
    retFile, retModuleNames = "", []
    for srcFile, modules in fileToModulesMap.items():
        if module in modules:
            retFile = srcFile
            retModuleNames = modules
            break
    assert retFile != ""
    retModules = getModuleDefAstNodes(vast, retModuleNames)
    return retFile, retModules

def getSpsLineno(ast, nodeIds, fileToModulesMap, lineGapMap):
    spsLinenos = set()
    t1 = [ast]
    modules = []
    while len(t1) > 0:
        t = t1.pop(0)
        if isinstance(t, ModuleDef):
            modules.append(t)
        elif isinstance(t, Source) or isinstance(t, Description):
            for childAst in t.children():
                t1.append(childAst)
    for module in modules:
        currentFile = None
        for fileName, modules2 in fileToModulesMap.items():
            if module.name in modules2:
                currentFile = fileName
        t2 = [module]
        while len(t2) > 0:
            t = t2.pop(0)
            if t.nodeid in nodeIds:
                spsLinenos.add((currentFile, t.lineno-lineGapMap[currentFile]))
            for childAst in t.children():
                t2.append(childAst)
    return spsLinenos