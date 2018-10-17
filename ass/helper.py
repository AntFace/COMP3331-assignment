from enum import Enum

# Classes
class State(Enum):
    CLOSED = 0
    LISTEN = 1
    SYN_SENT = 2
    SYN_RCVD = 3
    ESTABLISHED = 4
    FIN_WAIT_1 = 5
    FIN_WAIT_2 = 6
    TIME_WAIT = 7
    CLOSE_WAIT = 8
    LAST_ACK = 9

class Header:
    def __init__(self, seqNum=0, ackNum=0, checksum=0, ack=False, syn=False, fin=False):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.checksum = checksum
        self.ack = ack
        self.syn = syn
        self.fin = fin

class Segment:
    def __init__(self, header, payload=None):
        self.header = header
        self.payload = payload

    def __lt__(self, other):
        return self.header.seqNum < other.header.seqNum

    def __eq__(self, other):
        return self.header.seqNum == other.header.seqNum
