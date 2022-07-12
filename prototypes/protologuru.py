from loguru import logger
import sys

from support.loggercapture import LoggerCapture

logger.debug("testing, testing, one, two, three")


def from_fn():
    logger.info("info")
    logger.critical("oh dang oh jeez")


from_fn()

print("~~~")

logger.trace("trace...")  # does not print
logger.debug("debug?")
logger.info("info :v")
logger.success("success.")
logger.warning("warning!")
logger.error("error!!")
logger.critical("critical!!!")

logger.remove()
logger.add(sys.stderr, level="WARNING")

logger.trace("trace 2")  # you shouldn't see this
logger.error("error 2")

c = LoggerCapture()

cid = logger.add(c.receive)
print(cid)

logger.info("info message")

m = c.log[0]

print(c.log)
