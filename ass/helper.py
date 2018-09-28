from enum import Enum

# Classes
class State(Enum):
    INACTIVE = 0
    HANDSHAKE = 1
    CONNECTED = 2

class Header:
    def __init__(self, seqNum=0, ackNum=0, payloadLength=0, checksum=0, mws=0, mss=0, ack=0, syn=0, fin=0):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.payloadLength = payloadLength
        self.checksum = checksum
        self.mws = mws
        self.mss = mss
        self.ack = ack
        self.syn = syn
        self.fin = fin

    def encode(self):
        bits = '{0:032b}'.format(self.seqNum)
        bits += '{0:032b}'.format(self.ackNum)
        bits += '{0:032b}'.format(self.payloadLength)
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

    def encode(self):
        if self.payload:
            return self.header.encode() + self.payload
        else:
            return self.header.encode()

# Functions
def decode(encodedMessage):
    seqNum = int(encodedMessage[0:32], 2)
    ackNum = int(encodedMessage[32:64], 2)
    payloadLength = int(encodedMessage[64:96], 2)
    checksum = int(encodedMessage[96:112], 2)
    mws = int(encodedMessage[122:144], 2)
    mss = int(encodedMessage[144:176], 2)
    ack = int(encodedMessage[176:177], 2)
    syn = int(encodedMessage[177:178], 2)
    fin = int(encodedMessage[178:179], 2)

    header = Header(seqNum, ackNum, payloadLength, checksum, mws, mss, ack, syn, fin)

    if payloadLength:
        payload = encodedMessage[179:].decode('iso-8859-1')
        
        return Message(header, payload)
    else:
        return Message(header)
