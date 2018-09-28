import random
import socket
import sys
import time

from helper import *

class Sender:
    def __init__(self, receiverHost, receiverPort, filename, mws, mss, gamma):
        self.receiverHost = receiverHost
        self.receiverPort = receiverPort
        self.filename = filename
        self.mws = mws
        self.mss = mss
        self.gamma = gamma

        self.state = State.INACTIVE
        self.seqNum = 0

    def handshake(self): # three-way handshake (SYN, SYN+ACK, ACK)
        # Set up socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.receiverHost, self.receiverPort))
        self.socket.settimeout(1) # Set timeout to 1 for now

        while True:
            if self.state == State.INACTIVE:
                header = Header(self.seqNum, 0, 0, 0, 0, 0, 0, 1, 0) # SYN
                self.send(header=header)
                self.seqNum += 1
                self.state = State.HANDSHAKE
            elif self.state == State.HANDSHAKE:
                received = self.socket.recv(4096)
                receivedHeader = decode(received).header
                if receivedHeader.syn and receivedHeader.ack:
                    self.state = State.CONNECTED
            elif self.state == State.CONNECTED:
                header = Header(self.seqNum, 0, 0, 0, 0, 0, 1, 0, 0) # ACK
                self.send(header=header)
                self.seqNum += 1
                received = self.socket.recv(4096)
                break

    def send(self, header=None, payload=None):
        if payload:
            self.seqNum = header.seqNum + len(payload)
        message = Message(header, payload)
        self.socket.send(message.encode())

if __name__ == '__main__':
    if len(sys.argv) != 7 and len(sys.argv) != 15:
        print ('Incorrect number of arguments')
        sys.exit()

    receiverHost = sys.argv[1]
    receiverPort = int(sys.argv[2])
    filename = sys.argv[3]
    mws = int(sys.argv[4])
    mss = int(sys.argv[5])
    gamma = int(sys.argv[6])
    
    #PLD module arguments
    if len(sys.argv) == 15:
        pDrop = sys.argv[7]
        pDuplicate = sys.argv[8]
        pCorrupt = sys.argv[9]
        pOrder = sys.argv[10]
        maxOrder = sys.argv[11]
        pDelay = sys.argv[12]
        maxDelay = sys.argv[13]
        seed = int(sys.argv[14])
    
    sender = Sender(receiverHost, receiverPort, filename, mws, mss, gamma)
    sender.handshake()
