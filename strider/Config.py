import os

PROJECT_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")

TIMEOUT = 2

REPAIR_TIME = 7200
BENCHMARKS = os.path.join(PROJECT_PATH, "benchmarks")
WORK_DIR = os.path.join(PROJECT_PATH, "workdir")
PATCH_DIR = os.path.join(PROJECT_PATH, "patch")

LOG_PATH = os.path.join(PROJECT_PATH, "logs/strider.log")