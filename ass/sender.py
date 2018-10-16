import socket
import sys
import time

from helper import *
from logger import *
from pld import *
from timer import *

class Sender:
    def __init__(self, receiverHost, receiverPort, filename, mws, mss, gamma, pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed):
        self.receiverHost = receiverHost
        self.receiverPort = receiverPort
        self.filename = filename
        self.mws = mws
        self.mss = mss

        self.PLD = PLD(pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed)

        self.state = State.CLOSED
        self.seqNum = 0
        self.ackNum = 0

        self.filesize = 0
        self.payloads = self._prepareFile()

        self.logger = Logger('Sender_log.txt')
        self.timer = Timer(gamma=gamma)

        # Set up socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.receiverHost, self.receiverPort))
        self.socket.settimeout(self.timer.getTimeoutInterval())

    def handshake(self): # three-way handshake (SYN, SYN+ACK, ACK)
        while True:
            if self.state == State.CLOSED:
                header = Header(seqNum=self.seqNum, ackNum=self.ackNum, syn=True) # SYN
                self._send(header=header)
                print('SYN sent')
                self.state = State.SYN_SENT
            elif self.state == State.SYN_SENT:
                response = self._receive()
                responseHeader = response.header
                if responseHeader.syn and responseHeader.ack:
                    print('SYN+ACK received')
                    self.ackNum += 1
                    self.state = State.ESTABLISHED
            elif self.state == State.ESTABLISHED:
                self.seqNum += 1
                header = Header(seqNum=self.seqNum, ackNum=self.ackNum, ack=True) # ACK
                self._send(header=header)
                print('ACK sent')
                
                return

    def sendFile(self):
        print('Sending file...')
        nextSeqNum = initialSeqNum = self.seqNum
        while self.seqNum < initialSeqNum + self.filesize:
            if nextSeqNum - initialSeqNum < self.filesize:
                payload = self.payloads[nextSeqNum - initialSeqNum]
            else:
                payload = None
            if payload and nextSeqNum + len(payload) - self.seqNum <= self.mws:
                header = Header(seqNum=nextSeqNum, ackNum=self.ackNum)
                if not self.timer.isRunning:
                    self.timer.start()
                self._send(header=header, payload=payload, PLD=True)
                print('Sent Segment. Seq num: {}'.format(header.seqNum))
                nextSeqNum += len(payload)
            else:
                try:
                    response = self._receive()
                except socket.timeout:
                    print('Timed out!')
                    self.timer.discard()
                    header = Header(seqNum=self.seqNum, ackNum=self.ackNum)
                    payload = self.payloads[self.seqNum - initialSeqNum]
                    self._send(header=header, payload=payload, event='snd/RXT/timeout', PLD=True)
                    print('Re-sent Segment. Seq num: {}'.format(header.seqNum))
                    self.timer.start()
                else:
                    responseHeader = response.header
                    print('Received response. ACK num: {}'.format(responseHeader.ackNum))
                    if responseHeader.ackNum > self.seqNum:
                        self.seqNum = responseHeader.ackNum
                        if self.timer.isRunning:
                            self.timer.stop()
                            self._updateTimeout()

    def teardown(self):
        print('Teardown...')
        while True:
            if self.state == State.ESTABLISHED:
                header = Header(seqNum=self.seqNum, ackNum=self.ackNum, fin=True)
                self._send(header=header)
                print('FIN sent')
                self.state = State.FIN_WAIT_1
            elif self.state == State.FIN_WAIT_1:
                response = self._receive()
                responseHeader = response.header
                if responseHeader.ack:
                    print('ACK received')
                    self.state = State.FIN_WAIT_2
            elif self.state == State.FIN_WAIT_2:
                response = self._receive()
                responseHeader = response.header
                if responseHeader.fin:
                    print('FIN received')
                    self.seqNum += 1
                    self.ackNum += 1
                    header = Header(seqNum=self.seqNum, ackNum=self.ackNum, ack=True)
                    self._send(header=header)
                    print('ACK sent')
                    self.state = State.TIME_WAIT
            elif self.state == State.TIME_WAIT:
                self.logger.logFinal(sender=True)
                print('Waiting 10 seconds...')
                time.sleep(10)
                self.socket.close()
                print('Socket closed')
                self.state = State.CLOSED
                print('Teardown completed')

                return
                
    def _prepareFile(self):
        print('Reading {filename}'.format(filename=self.filename))
        with open(self.filename, mode='rb') as f:
            content = f.read()
        self.filesize = len(content)
        payloads = {}
        numPayloads = int(self.filesize / self.mss)
        if self.filesize % self.mss != 0:
            numPayloads += 1
        for i in range(0, numPayloads):
            payloads[i * self.mss] = content[self.mss * i : self.mss * (i + 1)]

        return payloads

    def _send(self, header=None, payload=None, event='snd', PLD=False):
        segment = Segment(header, payload)
        if PLD:
            if self.PLD.checkDrop():
                print('Dropping! Seq num: {}'.format(header.seqNum))
                if event == 'snd':
                    return self.logger.log('drop', segment)
                elif event == 'snd/RXT/timeout':
                    return self.logger.log('drop/RXT/timeout', segment)
        self.logger.log(event, segment)

        return self.socket.send(segment.encode())

    def _receive(self):
        response = decode(self.socket.recv(4096))
        self.logger.log('rcv', response)

        return response

    def _updateTimeout(self):
        return self.socket.settimeout(self.timer.getTimeoutInterval())

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
        pDrop = float(sys.argv[7])
        pDuplicate = float(sys.argv[8])
        pCorrupt = float(sys.argv[9])
        pOrder = float(sys.argv[10])
        maxOrder = int(sys.argv[11])
        pDelay = float(sys.argv[12])
        maxDelay = int(sys.argv[13])
        seed = int(sys.argv[14])
    
    sender = Sender(receiverHost, receiverPort, filename, mws, mss, gamma, pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed)
    sender.handshake()
    sender.sendFile()
    sender.teardown()
