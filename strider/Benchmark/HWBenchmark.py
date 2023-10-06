import os, copy
import Config
from utils import CmdUtils, FileUtils, StringUtils
from Benchmark import Benchmark
from VerilogAnalyzer import SignalAnalyzer, VcdAnalyzer

class HWBenchmark(Benchmark.Benchmark):
    def __init__(self, benchmark) -> None:
        super().__init__(benchmark)

    def test(self, srcFiles=None, tbFile=None):
        if srcFiles == None:
            srcFiles = self.bugInfoDict["src_file"]
        if tbFile == None:
            tbFile = self.bugInfoDict["test_bench"]
        # simCommand = "vcs -sverilog +vc -Mupdate -line -full64 {} {} -o simv -R -LDFLAGS -Wl,--no-as-needed".format(tbFile, " ".join(srcFiles))
        simCommand = "iverilog -o wave {} {}; timeout {} vvp -n wave; rm wave;".format(tbFile, " ".join(srcFiles), Config.TIMEOUT)
        result = CmdUtils.runCmd(simCommand, cwd=self.bugInfoDict["proj_dir"])
        if "syntax error" in result:
            raise SystemError("Syntax Error.")

    def validate(self, suspiciousFiles, candidatePatches):
        candidateSrcFiles = None
        for suspiciousFile, candidatePatch in zip(suspiciousFiles, candidatePatches):
            codeFilePath = os.path.join(Config.WORK_DIR, os.path.basename(suspiciousFile))
            canCodeFilePath = codeFilePath.replace(".v", "_can{}.v".format(StringUtils.genRandomString(4)))
            while(os.path.exists(canCodeFilePath)):
                canCodeFilePath = codeFilePath.replace(".v", "_can{}.v".format(StringUtils.genRandomString(4)))
            assert not os.path.exists(canCodeFilePath)
            candidateSrcFiles = copy.deepcopy(self.bugInfoDict["src_file"])
            for i, file in enumerate(candidateSrcFiles):
                if file == suspiciousFile:
                    candidateSrcFiles[i] = canCodeFilePath
            FileUtils.writeStrToFile(candidatePatch, canCodeFilePath)
        self.removeSimulationFiles()

        self.test(srcFiles=candidateSrcFiles)
        try:
            oracleSignal, simSignal = self.readSimulationOutput()
            if SignalAnalyzer.getMismatchSignal(oracleSignal, simSignal)[0] == None:
                return True, candidateSrcFiles
            return False, candidateSrcFiles
        except Exception as e:
            return False, candidateSrcFiles