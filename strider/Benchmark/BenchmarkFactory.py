from Benchmark.CirFixBenchmark import CirFixBenchmark
from Benchmark.HWBenchmark import HWBenchmark

def createBenchmark(benchmarkStr):
    benchmark = None
    if benchmarkStr.lower() == "cirfix_benchmarks":
        benchmark = CirFixBenchmark(benchmarkStr)
    else:
        benchmark = HWBenchmark(benchmarkStr)
    return benchmark