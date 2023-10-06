import sys, argparse, func_timeout
import Config
import Repair
import time
from utils import Logger, FileUtils
from Benchmark import BenchmarkFactory

def test(logger, benchmarkArg, projectArg, versionArg):
    benchmark = BenchmarkFactory.createBenchmark(benchmarkArg)
    try:
        bugInfo = benchmark.getBugInfo(projectArg, versionArg)
        logger.info("Start repair ...")
        Repair.repair(benchmark, bugInfo, logger)
        FileUtils.removeDirContent(Config.WORK_DIR)
    except func_timeout.exceptions.FunctionTimedOut:
        logger.error("{}_{} Repair timeout.".format(projectArg, versionArg))
    except Exception as e:
        logger.error("{}_{} Repair error.".format(projectArg, versionArg))
        logger.error(str(e))

def testAll(logger, benchmarkArg):
    benchmark = BenchmarkFactory.createBenchmark(benchmarkArg)
    allBugs = benchmark.getAllBugs()
    for project, version in allBugs:
        try:
            bugInfo = benchmark.getBugInfo(project, version)
            logger.info("Start Repair {} {}.".format(project, version))
            startTime = time.time()
            Repair.repair(benchmark, bugInfo, logger)
            endTime = time.time()
            logger.info("Repair Completed: {}s.".format(endTime-startTime))
            FileUtils.removeDirContent(Config.WORK_DIR)
        except func_timeout.exceptions.FunctionTimedOut:
            logger.error("{}_{} Repair timeout.".format(project, version))
        except Exception as e:
            logger.error("{}_{} Repair error.".format(project, version))
            logger.error(str(e))

if __name__ == "__main__":
    aparser = argparse.ArgumentParser()
    aparser.add_argument("-b", "--benchmark", help="Project")
    aparser.add_argument("-p", "--project", help="Project")
    aparser.add_argument("-v", "--version", help="Bug Id")
    logger = Logger.initLogger(Config.LOG_PATH)
    
    args = aparser.parse_args()
    logger.info(args)
    if args.benchmark == None:
        logger.error("No benchmark.")
        sys.exit(0)
    if args.project == None and args.version == None:
        testAll(logger, args.benchmark)
    else:
        if args.project == None:
            logger.error("No project.")
            sys.exit(0)
        if args.version == None:
            logger.error("No bug id.")
            sys.exit(0)
        test(logger, args.benchmark, args.project, args.version)