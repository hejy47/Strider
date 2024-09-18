import os, json, copy
from func_timeout import func_set_timeout
import Config
from utils import FileUtils, StringUtils
from VerilogAnalyzer import VcdAnalyzer, SignalAnalyzer, AstAnalyzer, DataFlowAnalyzer
from Locator.Locator import Locator
from Adapter.Adapter import Adapter

# def groupActions(allMismatchSignals, allActions, allParameterInfos, mismatchSignals):
#     retMismatchSignals, retActions, retParameterInfos = [[]], [[]], [[]]
#     for ms in mismatchSignals:
#         gMismatchSignals, gActions, gParameterInfos = [], [], []
#         for mis, act, par in zip(allMismatchSignals[ms], allActions[ms], allParameterInfos[ms]):
#             eMismatchSignals, eActions, eParameterInfos = copy.deepcopy(retMismatchSignals), copy.deepcopy(retActions), copy.deepcopy(retParameterInfos)
#             for retMis, retAct, retPar in zip(eMismatchSignals, eActions, eParameterInfos):
#                 retMis.append(mis)
#                 retAct.append(act)
#                 retPar.append(par)
#             gMismatchSignals.extend(eMismatchSignals)
#             gActions.extend(eActions)
#             gParameterInfos.extend(eParameterInfos)
#         retMismatchSignals, retActions, retParameterInfos = gMismatchSignals, gActions, gParameterInfos
#     return retMismatchSignals, retActions, retParameterInfos

def groupActions(allSuspiciousSignals, allActions, allParameterInfos):
    retSuspiciousSignals, retActions, retParameterInfos = [], [], []
    for ms in allSuspiciousSignals.keys():
        for mis, act, par in zip(allSuspiciousSignals[ms], allActions[ms], allParameterInfos[ms]):
            retSuspiciousSignals.append([mis])
            retActions.append([act])
            retParameterInfos.append([par])
    return retSuspiciousSignals, retActions, retParameterInfos

def locate(benchmark, bugInfo, logger):
    srcFiles = bugInfo["src_file"]
    benchmark.updateSrcFiles(srcFiles)

    logger.info("Running simulation.")
    benchmark.test(srcFiles=srcFiles)

    logger.info("Reading oracle and simulation output.")
    oracleSignal, simSignal = benchmark.readSimulationOutput()

    logger.info("processing VCD files.")
    # oracleVcd, simVcd, attributesDict = benchmark.readVcd()
    oracleVcdFile, simVcdFile, timeScale = benchmark.readVcd()

    allTerms, allBindDicts, allParameters = {}, {}, {}
    logger.info("AST parsing.")
    astArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"]}
    astParser = AstAnalyzer.AstParser(astArgs)
    ast = astParser.getAst()
    fileToModulesMap = AstAnalyzer.mapFileToModule(astArgs)
    lineGapMap = StringUtils.mapLineGapAfterProcess(astArgs)
    # ast.show()
    # modules, instances = AstAnalyzer.getModuleAndInstance(ast)
    
    dfArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"], "noreorder":True, "nobind":False}
    # for module in modules:
    for module, _ in bugInfo["top_module"].items():
        logger.info("Dataflow analyzing {}.".format(module))
        dfArgs["topmodule"] = module
        dfAnalyzer = DataFlowAnalyzer.DataFlowAnalyzer(dfArgs)
        terms = dfAnalyzer.getTerms()
        bindDicts = dfAnalyzer.getBindDicts()
        parameters = dfAnalyzer.getParameters()
        allTerms.update(terms)
        allBindDicts.update(bindDicts)
        allParameters.update(parameters)
        
    moduleInfo = VcdAnalyzer.getModuleInfo(bugInfo["top_module"])

    timeStamp, mismatchSignals, simVarsDict, attributesDict, oracleAttributesDict, prevSimSignalValue, tmpSimSignalValue, tmpOracleSignalValue = VcdAnalyzer.getMismatchSignal(oracleVcdFile, simVcdFile, timeScale)
    VcdAnalyzer.groupSimVarsDict(simVarsDict)
    VcdAnalyzer.MapIOSignals(simVarsDict, mismatchSignals, tmpOracleSignalValue)
    tmpInputSignalValues = VcdAnalyzer.getInputSignalValue(attributesDict, prevSimSignalValue, tmpSimSignalValue)
    # get input value for internal signals
    internalSignals = VcdAnalyzer.getInternalSignals(simVarsDict, oracleAttributesDict)
    tmpInputInternalSignalValues = VcdAnalyzer.getInputValueOfInternalSignals(timeStamp, internalSignals, simVcdFile, timeScale)
    tmpInputSignalValues.update(tmpInputInternalSignalValues)

    logger.info("Locating suspicious df nodes.")
    locator = Locator(timeStamp, mismatchSignals, allBindDicts, allTerms, allParameters, moduleInfo)
    locator.locate(tmpInputSignalValues, tmpOracleSignalValue)
    suspiciousNodeIds = locator.getSpsNodeIds()
    suspiciousLinenos = AstAnalyzer.getSpsLineno(ast, suspiciousNodeIds, fileToModulesMap, lineGapMap)
    tmpLinenos = [i[1] for i in suspiciousLinenos]
    logger.info("Suspicious Lines: {}".format(tmpLinenos))
    benchmark.removeSimulationFiles()

@func_set_timeout(Config.REPAIR_TIME)
def repair(benchmark, bugInfo, logger):
    candidateSrcFilesList = [bugInfo["src_file"]]
    while len(candidateSrcFilesList) > 0:
        srcFiles = candidateSrcFilesList.pop(0)
        benchmark.updateSrcFiles(srcFiles)

        logger.info("Running simulation.")
        benchmark.test(srcFiles=srcFiles)

        logger.info("Reading oracle and simulation output.")
        oracleSignal, simSignal = benchmark.readSimulationOutput()
        outputTimeStamp, _ = SignalAnalyzer.getMismatchSignal(oracleSignal, simSignal)

        logger.info("processing VCD files.")
        # oracleVcd, simVcd, attributesDict = benchmark.readVcd()
        oracleVcdFile, simVcdFile, timeScale = benchmark.readVcd()

        allTerms, allBindDicts, allParameters = {}, {}, {}
        logger.info("AST parsing.")
        astArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"]}
        astParser = AstAnalyzer.AstParser(astArgs)
        ast = astParser.getAst()
        ast.show()
        # modules, instances = AstAnalyzer.getModuleAndInstance(ast)
        fileToModulesMap = AstAnalyzer.mapFileToModule(astArgs)
        
        dfArgs = {"filelist":srcFiles, "include":bugInfo["include_list"], "define":bugInfo["define_list"], "noreorder":True, "nobind":False}
        # for module in modules:
        for module, _ in bugInfo["top_module"].items():
            logger.info("Dataflow analyzing {}.".format(module))
            dfArgs["topmodule"] = module
            dfAnalyzer = DataFlowAnalyzer.DataFlowAnalyzer(dfArgs)
            terms = dfAnalyzer.getTerms()
            bindDicts = dfAnalyzer.getBindDicts()
            parameters = dfAnalyzer.getParameters()
            allTerms.update(terms)
            allBindDicts.update(bindDicts)
            allParameters.update(parameters)

        moduleInfo = VcdAnalyzer.getModuleInfo(bugInfo["top_module"])

        timeStamp, mismatchSignals, simVarsDict, attributesDict, oracleAttributesDict, prevSimSignalValue, tmpSimSignalValue, tmpOracleSignalValue = VcdAnalyzer.getMismatchSignal(oracleVcdFile, simVcdFile, timeScale)
        VcdAnalyzer.groupSimVarsDict(simVarsDict)
        VcdAnalyzer.MapIOSignals(simVarsDict, mismatchSignals, tmpOracleSignalValue)
        tmpInputSignalValues = VcdAnalyzer.getInputSignalValue(attributesDict, prevSimSignalValue, tmpSimSignalValue)
        # get input value for internal signals
        internalSignals = VcdAnalyzer.getInternalSignals(simVarsDict, oracleAttributesDict)
        tmpInputInternalSignalValues = VcdAnalyzer.getInputValueOfInternalSignals(timeStamp, internalSignals, simVcdFile, timeScale)
        tmpInputSignalValues.update(tmpInputInternalSignalValues)

        logger.info("Locating suspicious df nodes.")
        locator = Locator(timeStamp, mismatchSignals, allBindDicts, allTerms, allParameters, moduleInfo)
        locator.locate(tmpInputSignalValues, tmpOracleSignalValue)

        suspiciousSignals = locator.getSuspiciousSignals()
        locatedbindDicts = locator.getBindDicts()
        executedPaths = locator.getExecutedPaths()
        availableTerms = locator.getAvailableTerms()
        availableParameters = locator.getAvailableParameters()
        availableRenameInfo = locator.getAvailableRenameInfo()

        logger.info("Repairing suspicious nodes.")
        posExpectedSignalValues = {}
        allSuspiciousSignals, allActions, allParameterInfos = {}, {}, {}
        # for ss, ats, aps, ars, bds, eps in zip(suspiciousSignals, availableTerms, availableParameters, availableRenameInfo, locatedbindDicts, executedPaths):
        for i, ss in enumerate(suspiciousSignals):
            ssIndex = suspiciousSignals.index(ss)
            ats, aps, ars, bds, eps = availableTerms[ssIndex], availableParameters[ssIndex], availableRenameInfo[ssIndex], locatedbindDicts[ssIndex], executedPaths[ssIndex]
            # skip the signal whose binddicts are not located
            if bds == []: continue
            allSuspiciousSignals[ss], allActions[ss], allParameterInfos[ss] = [], [], []
            subInstance = ss[:ss.rindex('.')]
            adapter = Adapter()

            ssTmpInputSignalValue = {}
            if ss in tmpInputSignalValues:
                ssTmpInputSignalValue = tmpInputSignalValues[ss]
            ssTmpOracleSignalValues = []
            if ss in tmpOracleSignalValue:
                ssTmpOracleSignalValues = [tmpOracleSignalValue[ss]]
            else:
                # transfer to signal without tb
                tmpss = ss[ss.index('.')+1:]
                index = tmpss.index('.')
                instance, signal = tmpss[:index], tmpss[index+1:]
                moduless = "{}.{}".format(moduleInfo[instance], signal)
                if moduless in posExpectedSignalValues:
                    ssTmpOracleSignalValues = copy.deepcopy(posExpectedSignalValues[moduless])
            
            # DEBUG
            if ss == "tst_bench_top.i2c_slave.state" or ssTmpOracleSignalValues == []:
                print("debug", ss)
                
            # msPrevTmpInputSignalValue, msPostTmpInputSignalValue = prevTmpInputSignalValue[ms], postTmpInputSignalValue[ms]
            # msPrevTmpOracleSignalValue, msPostTmpOracleSignalValue= prevTmpOracleSignalValue[ms], postTmpOracleSignalValue[ms]
            for ssTmpOracleSignalValue in ssTmpOracleSignalValues:
                for at, ap, ar, bd, ep in zip(ats, aps, ars, bds, eps):
                    sbd = copy.deepcopy(bd)
                    candidateBindDicts, tmpPosExpectedSignalValues = adapter.synthesize(subInstance, ssTmpOracleSignalValue, ssTmpInputSignalValue, attributesDict, at, ap, ar, sbd, ep, bindDicts)
                    for cbd in candidateBindDicts:
                        actions = adapter.adaptBindDict(bd, cbd)
                        allSuspiciousSignals[ss].append((cbd.dest, cbd.lsb, cbd.msb, cbd.ptr))
                        allActions[ss].append(actions)
                        allParameterInfos[ss].append(cbd.parameterinfo)
                    # update the possible expected signal values
                    for signal, posExpectedValues in tmpPosExpectedSignalValues.items():
                        updateFlag = False
                        if signal in posExpectedSignalValues:
                            for posExpectedValue in posExpectedValues:
                                if posExpectedValue not in posExpectedSignalValues[signal]:
                                    posExpectedSignalValues[signal].append(posExpectedValue)
                                    updateFlag = True
                        else:
                            posExpectedSignalValues[signal] = posExpectedValues
                            updateFlag = True
                        if updateFlag:
                            instanceSignal = subInstance + signal[signal.rindex('.'):]
                            # the expected values of the signal are updated, retry to synthesize it
                            if instanceSignal in suspiciousSignals and instanceSignal not in suspiciousSignals[i+1:]:
                                suspiciousSignals.append(instanceSignal)
        groupAllSuspiciousSignals, groupAllActions, groupAllParameterInfos = groupActions(allSuspiciousSignals, allActions, allParameterInfos)
        patialPatchNum = 0
        for gSuspiciousSignals, gActions, gParameterInfos in zip(groupAllSuspiciousSignals, groupAllActions, groupAllParameterInfos):
            adapter.adaptAst(copy.deepcopy(ast), gSuspiciousSignals, gParameterInfos, gActions, fileToModulesMap)
            logger.info("Generating code.")
            suspiciousFiles, newAsts = adapter.getPatchAst()
            generator = AstAnalyzer.AstGenerator()
            newCodes = []
            try:
                for newAst in newAsts:
                    newCode = generator.visit(newAst)
                    newCodes.append(newCode)
                    # logger.info("Validate candidate patched code:\n{}".format(newCode))
                validateFlag, candidateSrcFiles = benchmark.validate(suspiciousFiles, newCodes)
                if validateFlag:
                    bugId = benchmark.getBugId()
                    patchDir = os.path.join(Config.PATCH_DIR, *bugId)
                    for candidateSrcFile in candidateSrcFiles:
                        if Config.WORK_DIR in candidateSrcFile:
                            baseCandidateSrcFile = StringUtils.subString("_can\d{4}", "", os.path.basename(candidateSrcFile))
                            FileUtils.moveFile(candidateSrcFile, os.path.join(patchDir, baseCandidateSrcFile))
                    logger.info("Repair success.")
                    return
                else:
                    oracleSignal, simSignal = benchmark.readSimulationOutput()
                    tmpTimeStamp, _ = SignalAnalyzer.getMismatchSignal(oracleSignal, simSignal)
                    # tmpTimeStamp = VcdAnalyzer.getMismatchSignal(oracleVcdFile, simVcdFile, timeScale)[0]
                    if int(tmpTimeStamp) > int(outputTimeStamp) and patialPatchNum < 5:
                        # keep the file
                        logger.info("Keep the modified file.")
                        patialPatchNum += 1
                        candidateSrcFilesList.append(candidateSrcFiles)
                    else:
                        for candidateSrcFile in candidateSrcFiles:
                            if Config.WORK_DIR in candidateSrcFile:
                                FileUtils.removeFile(candidateSrcFile)
                        logger.info("Repair failed.")
            except Exception as e:
                logger.error(str(e))
                logger.info("AST parse, compile or simulate failed!")
        
        benchmark.removeSimulationFiles()