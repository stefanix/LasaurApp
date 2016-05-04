""" remotelogger.py

A Wrapper around the influxdb client, if influxdb is not available it will fallback to stdout.

"""

from __future__ import print_function
from datetime import datetime

INFLUXDB_ENABLED = False
INFLUXDB_LOG_ENABLED = False
try:
    from influxdb import InfluxDBClient
    INFLUXDB_ENABLED = True
except ImportError:
    print("[TimeMonitor] No InfluxDB Installed, ",
        "if you want remote logging, please install 'pip install influxdb'")

class RemoteLogger(object):
    """ The RemoteLogger is able to log to influxdb or stdout.
    Args:
        channel - the name of the channel to log into
        config - a dict containing values for: host, port, user, pw, db
    """

    def __init__(self, channel, config):
        self.channel = channel

        INFLUXDB_LOG_ENABLED = (config != False and INFLUXDB_ENABLED)

        if INFLUXDB_LOG_ENABLED:
            self.client = InfluxDBClient(
                config["host"],
                config["port"],
                config["user"],
                config["pw"],
                config["db"])

    def log(self, *args):
        """ logs a message to influxdb or stdout. Uses the logl level LOG """

        message = str.join(" ", [str(elem) for elem in args])

        if INFLUXDB_LOG_ENABLED:
            self.client.write_points([{
                "name": "lasersaur",
                "level": "LOG",
                "timestamp": datetime.now().isoformat(),
                "channel": self.channel,
                "message": message
            }])
        else:
            print("[LOG] " + message)

    def info(self, *args):
        """ logs a message to influxdb or stdout. Uses the logl level INFO """

        message = str.join(" ", [str(elem) for elem in args])

        if INFLUXDB_LOG_ENABLED:
            self.client.write_points([{
                "name": "lasersaur",
                "level": "INFO",
                "timestamp": datetime.now().isoformat(),
                "channel": self.channel,
                "message": message
            }])
        else:
            print("[INFO] " + message)
