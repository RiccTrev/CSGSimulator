from datetime import datetime
import time
from dateutil import parser

def checkDateError(date: str) -> bool:
    try:
        parser.parse(date)
    except:
        return True
    return False

def checkValidTime(date: str) -> bool:
    unix_timestamp = int(parser.parse(date).timestamp())
    if unix_timestamp < 1092873600 or int(time.time()) < unix_timestamp:
        return True
    else:
        return False