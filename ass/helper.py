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
    def __init__(self, seqNum=0, ackNum=0, ack=False, syn=False, fin=False):
        self.seqNum = seqNum
        self.ackNum = ackNum
        self.ack = ack
        self.syn = syn
        self.fin = fin
        
        self.checksum = 0

class Segment:
    def __init__(self, header, payload=None):
        self.header = header
        self.payload = payload
        if self.payload:
            self._generateChecksum()

    # Sets checksum as one's complement of calculated checksum
    def _generateChecksum(self):
        self.header.checksum = getChecksum(self.payload) ^ 0xffff
        
# Functions
def getChecksum(payload):
    length = len(payload)

    # If odd number of bytes, add last byte first, right-padded with 0's
    if length % 2 != 0:
        length -= 1
        checksum = payload[length] << 8
    else:
        checksum = 0

    # Treat every two bytes as one 16-bit value and add to checksum
    for i in range(0, length, 2):
        checksum += (payload[i] << 8) + payload[i + 1]
        checksum = checksum + (checksum >> 16)

    return checksum
