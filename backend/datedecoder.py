from __future__ import print_function
import json
import base64
import calendar
import collections
import datetime
import json
import re
import uuid



def default(obj):
    # We preserve key order when rendering SON, DBRef, etc. as JSON by
    # returning a SON for those types instead of a dict.
    if isinstance(obj, datetime.datetime):
        timestamp = obj.strftime('%Y-%m-%dT%H:%M:%S')
        return {"$date": timestamp}
    if isinstance(obj, (RE_TYPE, Regex)):
        flags = ""
        if obj.flags & re.IGNORECASE:
            flags += "i"
        if obj.flags & re.LOCALE:
            flags += "l"
        if obj.flags & re.MULTILINE:
            flags += "m"
        if obj.flags & re.DOTALL:
            flags += "s"
        if obj.flags & re.UNICODE:
            flags += "u"
        if obj.flags & re.VERBOSE:
            flags += "x"
        if isinstance(obj.pattern, text_type):
            pattern = obj.pattern
        else:
            pattern = obj.pattern.decode('utf-8')
        return SON([("$regex", pattern), ("$options", flags)])
    if isinstance(obj, Binary):
        return SON([
            ('$binary', base64.b64encode(obj).decode()),
            ('$type', "%02x" % obj.subtype)])
    if PY3 and isinstance(obj, bytes):
        return SON([
            ('$binary', base64.b64encode(obj).decode()),
            ('$type', "00")])
    if isinstance(obj, uuid.UUID):
        return {"$uuid": obj.hex}
    raise TypeError("%r is not JSON serializable" % obj)


def object_hook(dct):
    if "$date" in dct:
        dtm = dct["$date"]
        if isinstance(dtm, basestring):
            aware = datetime.datetime.strptime(dtm[:19], "%Y-%m-%dT%H:%M:%S")
            return aware
        else:
            secs = float(dtm) / 1000.0
            return datetime.timedelta(seconds=secs)
    if "$regex" in dct:
        flags = 0
        # PyMongo always adds $options but some other tools may not.
        for opt in dct.get("$options", ""):
            flags |= _RE_OPT_TABLE.get(opt, 0)
        return Regex(dct["$regex"], flags)
    if "$binary" in dct:
        if isinstance(dct["$type"], int):
            dct["$type"] = "%02x" % dct["$type"]
        subtype = int(dct["$type"], 16)
        if subtype >= 0xffffff80:  # Handle mongoexport values
            subtype = int(dct["$type"][6:], 16)
        return Binary(base64.b64decode(dct["$binary"].encode()), subtype)
    if "$uuid" in dct:
        return uuid.UUID(dct["$uuid"])
    if "$undefined" in dct:
        return None
    return dct
