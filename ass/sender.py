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

        self.state = State.CLOSED
        self.seqNum = 0

        self.payloads = self._prepareFile()

    def handshake(self): # three-way handshake (SYN, SYN+ACK, ACK)
        # Set up socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.receiverHost, self.receiverPort))
        self.socket.settimeout(1) # Set timeout to 1 for now

        while True:
            if self.state == State.CLOSED:
                header = Header(seqNum=self.seqNum, syn=True) # SYN
                self._send(header=header)
                self.seqNum += 1
                self.state = State.SYN_SENT
                print('SYN sent')
            elif self.state == State.SYN_SENT:
                received = self._receive()
                receivedHeader = decode(received).header
                if receivedHeader.syn and receivedHeader.ack:
                    print('SYN+ACK received')
                    self.state = State.ESTABLISHED
            elif self.state == State.ESTABLISHED:
                header = Header(seqNum=self.seqNum, ack=True) # ACK
                print('ACK sent')
                self._send(header=header)
                self.seqNum += 1
                received = self._receive()
                break

    def sendFile(self):
        print('Sending file...')
        for payload in self.payloads:
            header = Header(seqNum=self.seqNum, payloadLength=len(payload))
            self._send(header, payload)
            try:
                response = decode(self._receive())
                print('Received response. ACK num: {}'.format(response.header.ackNum))
                responseHeader = response.header
                if responseHeader.ackNum == self.seqNum:
                    print('ACK for {} received'.format(self.seqNum))
            except socket.timeout:
                print('Timed out!')

    def teardown(self):
        print('Teardown...')
            
    def _prepareFile(self):
        print('Reading {filename}'.format(filename=self.filename))
        with open(self.filename, mode='rb') as f:
            content = f.read()

        return [content[self.mss * i:self.mss * (i + 1)] for i in range(0, int(len(content) / self.mss + 1))]

    def _send(self, header=None, payload=None):
        if payload:
            self.seqNum = header.seqNum + len(payload)
        message = Message(header, payload)
        self.socket.send(message.encode())

    def _receive(self):
        return self.socket.recv(4096)

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
    sender.sendFile()
    sender.teardown()
