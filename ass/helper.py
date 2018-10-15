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
    def __init__(self, seqNum=0, ackNum=0, checksum=0, mws=0, mss=0, ack=False, syn=False, fin=False):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.checksum = checksum
        self.mws = mws
        self.mss = mss
        self.ack = ack
        self.syn = syn
        self.fin = fin

    def encode(self):
        bits = '{0:032b}'.format(self.seqNum)
        bits += '{0:032b}'.format(self.ackNum)
        bits += '{0:016b}'.format(self.checksum)
        bits += '{0:032b}'.format(self.mws)
        bits += '{0:032b}'.format(self.mss)
        bits += '{0:01b}'.format(self.ack)
        bits += '{0:01b}'.format(self.syn)
        bits += '{0:01b}'.format(self.fin)
        
        return bits.encode()

class Message:
    def __init__(self, header, payload=None):
        self.header = header
        self.payload = payload

    def __lt__(self, other):
        return self.header.seqNum < other.header.seqNum

    def __eq__(self, other):
        return self.header.seqNum == other.header.seqNum

    def encode(self):
        if self.payload:
            return self.header.encode() + self.payload
        else:
            return self.header.encode()

# Functions
def decode(encodedMessage):
    seqNum = int(encodedMessage[0:32], 2)
    ackNum = int(encodedMessage[32:64], 2)
    checksum = int(encodedMessage[64:80], 2)
    mws = int(encodedMessage[80:112], 2)
    mss = int(encodedMessage[112:144], 2)
    ack = int(encodedMessage[144:145], 2)
    syn = int(encodedMessage[145:146], 2)
    fin = int(encodedMessage[146:147], 2)

    header = Header(seqNum, ackNum, checksum, mws, mss, ack, syn, fin)

    if len(encodedMessage) > 146:
        payload = encodedMessage[147:].decode('iso-8859-1')
        
        return Message(header, payload)
    else:
        return Message(header)
