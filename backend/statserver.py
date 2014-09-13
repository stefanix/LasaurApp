
import sys
import time
import threading
import logging
from config import conf
from websocket.server.SimpleWebSocketServer import WebSocket, SimpleWebSocketServer

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)

_server = None
_serverthread = None
_serverlock = threading.Lock()
_stop_server = False
_messagethread = None
_messageglock = threading.Lock()
_message = None
_stop_messager = False



class SimpleEcho(WebSocket):

    def handleMessage(self):
        if self.data is None:
            self.data = ''
        
        try:
            self.sendMessage(str(self.data))
        except Exception as n:
            print n
                 
    def handleConnected(self):
        print self.address, 'connected'
        self.sendMessage()

    def handleClose(self):
        print self.address, 'closed'



def start():
    global _server, _serverthread, _serverlock, _stop_server, \
           _message, _messagethread, _messageglock, _stop_messager

    ### server thread
    _stop_server = False
    _server = SimpleWebSocketServer(conf['network_host'], conf['websocket_port'], SimpleEcho)

    def run_server():
        global _server, _serverlock, _stop_server
        while True:
            with _serverlock:
                _server.process(timeout=0.01)
                if _stop_server:
                    break
            # sys.stdout.flush()

    _serverthread = threading.Thread(target=run_server)
    _serverthread.deamon = True  # kill thread when main thread exits
    _serverthread.start()
    print "INFO: status server online on port %s" % (conf['websocket_port'])

    ### messager thread
    _stop_messager = False
    def run_messager():
        global _server, _serverlock, \
               _message, _messagethread, _messageglock, _stop_messager
        message_cache = None
        while True:
            with _messageglock:
                if _stop_messager:
                    break
                if _message:
                    message_cache = _message
                    _message = None
            if message_cache:
                with _serverlock:
                    # broadcast message
                    for client in _server.connections.itervalues():
                        try:
                            client.sendMessage(message_cache)
                        except Exception as n:
                            print n
                message_cache = None
            time.sleep(0.01)
            # sys.stdout.flush()

    _messagethread = threading.Thread(target=run_messager)
    _messagethread.deamon = True  # kill thread when main thread exits
    _messagethread.start()



def stop():
    global _server, _serverthread, _serverlock, _stop_server, \
           _messagethread, _messageglock, _stop_messager
    
    with _messageglock:
        _stop_messager = True
    _messagethread.join()
    print "Status message thread stopped."
    _messagethread = None

    with _serverlock:
        _stop_server = True
    _serverthread.join()
    print "Status server thread stopped."
    _serverthread = None
    _server.close()
    _server = None



def send(msg):
    """Broadcast a message to all clients.
    This function is low-latency optimized by delegating the sending 
    process to a different thread. Even the locking is optimized
    with some caching.
    """
    global _message, _messageglock
    with _messageglock:
        _message = msg
