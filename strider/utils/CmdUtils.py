import subprocess
import logging, time

def runCmd(cmd, cwd=None, logger=None):
    if logger == None: logger = logging.getLogger()
    startTime = time.time()
    logger.info("cmd to run: {}".format(cmd))
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    try:
        output = p.stdout.decode("utf-8")
    except UnicodeDecodeError:
        logger.warn("cmd UnicodeDecoderError")
        output = p.stdout.decode("unicode_escape")
    error = p.stderr.decode("utf-8")
    if len(error) > 0:
        logger.error("output error: {}".format(error))
        output = error
    
    if len(output) > 0:
        logger.info("output of this cmd:\n{}".format(output))
    
    logger.info("cmd execution time: {}".format(time.time() - startTime))
    return output