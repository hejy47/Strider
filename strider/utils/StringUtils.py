import os, re, random
import string
import Config
from utils import CmdUtils, FileUtils

def removeComment(content):
    pattern1 = "/\*.*?\*/"
    pattern2 = "//.*?\n"
    content = re.sub(pattern1, "\n", content)
    content = re.sub(pattern2, "\n", content)
    return content

def genRandomString(length=4):
    retList = random.sample(string.digits, length)
    return ''.join(retList)

def subString(pattern, repl, dstString):
    return re.sub(pattern, repl, dstString)

def mapLineGapAfterProcess(args):
    fileLineMap = {}
    includeCmd = ""
    for includeDir in args["include"]:
        includeCmd = "-I {}".format(includeDir)
    defineCmd = ""
    for defineDir in args["define"]:
        defineCmd = "-I {}".format(defineDir)
    processCmd = "iverilog {} {} -E -o pp.out {}".format(includeCmd, defineCmd, " ".join(args["filelist"]))
    CmdUtils.runCmd(processCmd, cwd=Config.WORK_DIR)
    allFileContent = FileUtils.readFileToStr(os.path.join(Config.WORK_DIR, "pp.out"))
    for srcFile in args["filelist"]:
        srcFileContent = FileUtils.readFileToStr(srcFile)
        # tmpModuleContent = re.search("module .*?\(.*?\) *;", srcFileContent, re.S)[0]
        result = re.search("(module[ |\t].*?)\(.*?\) *;", srcFileContent, re.S)
        if result == None: continue
        tmpModuleContent = result[1]
        assert tmpModuleContent in allFileContent
        index1, index2 = srcFileContent.index(tmpModuleContent), allFileContent.index(tmpModuleContent)
        lineno1, lineno2 = srcFileContent[:index1].count("\n"), allFileContent[:index2].count("\n")
        fileLineMap[srcFile] = lineno2 - lineno1
    return fileLineMap

def transferCode(newCode):
    pattern = "\[([^:]*?):\\1\+([^:]*?)\]"
    result = re.findall(pattern, newCode, re.DOTALL)
    for r in result:
        oriSnippet = "[{}:{}+{}]".format(r[0],r[0],r[1])
        tSnippet = "[{}+:{}]".format(r[0],r[1])
        assert oriSnippet in newCode
        newCode = newCode.replace(oriSnippet, tSnippet, 1)
    return newCode