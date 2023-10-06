import os
import shutil
import logging

logger = logging.getLogger()

def readFileToStr(filePath):
    assert os.path.exists(filePath)
    fileStr = ""
    with open(filePath, 'r') as f:
        fileStr = f.read()
    return fileStr

def readFileToLines(filePath):
    assert os.path.exists(filePath)
    fileLines = []
    with open(filePath, 'r') as f:
        fileLines = f.readlines()
    return fileLines

def removeFile(filePath):
    if os.path.exists(filePath):
        assert os.path.isfile(filePath)
        os.remove(filePath)

def removeDir(dirPath):
    if os.path.exists(dirPath):
        assert os.path.isdir(dirPath)
        shutil.rmtree(dirPath)

def removeDirContent(dirPath):
    if os.path.exists(dirPath):
        assert os.path.isdir(dirPath)
        shutil.rmtree(dirPath)
        mkDir(dirPath)

def mkDir(dirPath):
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)

def mkDirFromFilePath(filePath):
    dirPath = os.path.dirname(filePath)
    if not os.path.exists(dirPath):
        os.makedirs(dirPath)

def writeStrToFile(fileStr, filePath, append=False):
    mkDirFromFilePath(filePath)
    mode = 'w'
    if append: mode = "a+"
    with open(filePath, mode) as f:
        f.write(fileStr)

def backupFile(srcFile, dstFile):
    assert os.path.isfile(srcFile)
    removeFile(dstFile)
    shutil.copyfile(srcFile, dstFile)

def moveFile(srcFile, dstFile):
    assert os.path.isfile(srcFile)
    mkDirFromFilePath(dstFile)
    shutil.copyfile(srcFile, dstFile)
    removeFile(srcFile)