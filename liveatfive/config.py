import datetime
import pytz

GOAL_TIME = datetime.time(17, 0, 0)
BUFFER = 15
EXTRA_TIME = True
TIMEZONE_NAME = "America/Los_Angeles"
TIMEZONE = pytz.timezone(TIMEZONE_NAME)

CREATOR = "itswill"
CREATOR_ID = 43246220

ONTIME_START = (datetime.datetime.combine(datetime.date.today(), GOAL_TIME) - datetime.timedelta(minutes=BUFFER)).time()
ONTIME_END   = (datetime.datetime.combine(datetime.date.today(), GOAL_TIME) + datetime.timedelta(minutes=BUFFER, seconds =59 if EXTRA_TIME else 0)).time()