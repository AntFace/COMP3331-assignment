import pickle
import socket
import sys
import time

from helper import *
from logger import *
from pld import *
from timer import *

class Sender:
    def __init__(self, receiverHost, receiverPort, filename, mws, mss, gamma, pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed):
        # Command line args
        self.receiverHost = receiverHost
        self.receiverPort = receiverPort
        self.filename = filename
        self.mws = mws
        self.mss = mss

        # State attributes
        self.state = State.CLOSED
        self.seqNum = 0
        self.ackNum = 0

        # File properties
        self.filesize = 0
        self.payloads = self._prepareFile()

        # Instantiate Logger and Timer
        self.logger = Logger('Sender_log.txt')
        self.timer = Timer(gamma=gamma)

        # Set up socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.connect((self.receiverHost, self.receiverPort))
        self.socket.settimeout(0.1) # Set socket timeout as a prompt to check the Timer module's actual timeout

        # Instantiate PLD Module - reference to socket and logger parsed so PLD can send and log appropriately
        self.PLD = PLD(pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed, self.socket, self.logger)

    def handshake(self): # Three-way handshake (SYN, SYN+ACK, ACK)
        while True:
            if self.state == State.CLOSED:
                header = Header(seqNum=self.seqNum, ackNum=self.ackNum, syn=True) # Send SYN
                self._send(header=header)
                print('SYN sent')
                self.state = State.SYN_SENT
            elif self.state == State.SYN_SENT:
                response = self._receive()
                responseHeader = response.header
                if responseHeader.syn and responseHeader.ack: # Receive SYN+ACK
                    print('SYN+ACK received')
                    self.ackNum += 1
                    self.state = State.ESTABLISHED
            elif self.state == State.ESTABLISHED:
                self.seqNum += 1
                header = Header(seqNum=self.seqNum, ackNum=self.ackNum, ack=True) # Send ACK
                self._send(header=header)
                print('ACK sent')
                
                return

    def sendFile(self): # Send file
        print('Sending file...')
        nextSeqNum = initialSeqNum = self.seqNum # self.seqNum tracks ACKs received
        duplicateACK = 0
        # While file has not been entirely received
        while self.seqNum < initialSeqNum + self.filesize:
            # Send up to MWS
            if nextSeqNum - initialSeqNum < self.filesize: # Retrieve payload if MWS has not shifted past the end of the file
                payload = self.payloads[nextSeqNum - initialSeqNum]
            else:
                payload = None
            if payload and nextSeqNum + len(payload) - self.seqNum <= self.mws: # Check MWS
                header = Header(seqNum=nextSeqNum, ackNum=self.ackNum)
                print('Seq num: {} sending...'.format(header.seqNum))
                self._send(header=header, payload=payload, PLD=True)
                nextSeqNum += len(payload)
                self.timer.start(RXT=False, nextSeqNum=nextSeqNum)
            else: # Try receive
                try:
                    response = self._receive()
                except socket.timeout: # If no ACK received, check Timer module's timeout
                    if self.timer.isTimedOut: # If timed out, timeout retransmission of lowest un-ACKed segment
                        print('Timed out!')
                        header = Header(seqNum=self.seqNum, ackNum=self.ackNum)
                        payload = self.payloads[self.seqNum - initialSeqNum]
                        print('Seq num: {} resending...'.format(header.seqNum))
                        self._send(header=header, payload=payload, event='timeoutRXT', PLD=True)
                        self.timer.start(RXT=True)
                else: # Response received
                    responseHeader = response.header
                    print('Received response. ACK num: {}'.format(responseHeader.ackNum))
                    if responseHeader.ack and responseHeader.ackNum > self.seqNum: # If ACK is larger than last received ACK, update self.seqNum to shift send window
                        duplicateACK = 0
                        self.seqNum = responseHeader.ackNum
                        self.timer.update(self.seqNum)
                    else: # Otherwise ACK is a duplicate
                        duplicateACK += 1
                        if duplicateACK == 3: # If third duplicate ACK, fast retransmission of lowest un-ACKed segment
                            print('Fast Retransmit!')
                            duplicateACK = 0
                            header = Header(seqNum=self.seqNum, ackNum = self.ackNum)
                            payload = self.payloads[self.seqNum - initialSeqNum]
                            print('Seq num: {} resending...'.format(header.seqNum))
                            self._send(header=header, payload=payload, event='fastRXT', PLD=True)
                            self.timer.start(RXT=True)

    def teardown(self): # Four segment connection termination 
        print('Teardown...')
        while True:
            if self.state == State.ESTABLISHED: # Send FIN
                header = Header(seqNum=self.seqNum, ackNum=self.ackNum, fin=True)
                self._send(header=header)
                print('FIN sent')
                self.state = State.FIN_WAIT_1
            elif self.state == State.FIN_WAIT_1: # Receive ACK
                response = self._receive()
                responseHeader = response.header
                if responseHeader.ack:
                    print('ACK received')
                    self.state = State.FIN_WAIT_2
            elif self.state == State.FIN_WAIT_2: # Receive FIN
                response = self._receive()
                responseHeader = response.header
                if responseHeader.fin: # Send ACK
                    print('FIN received')
                    self.seqNum += 1
                    self.ackNum += 1
                    header = Header(seqNum=self.seqNum, ackNum=self.ackNum, ack=True)
                    self._send(header=header)
                    print('ACK sent')
                    self.state = State.TIME_WAIT
            elif self.state == State.TIME_WAIT: # Wait and close
                self.PLD.shutdown()
                self.logger.logFinal(sender=True)
                print('Waiting 10 seconds...')
                time.sleep(10)
                self.socket.close()
                print('Socket closed')
                self.state = State.CLOSED
                print('Teardown completed')

                return
                
    def _prepareFile(self): # Splits file into chunks of size MSS and writes to a dictionary. Key: <number of first byte in chunk> Value: <chunk of MSS size>
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

    def _send(self, header=None, payload=None, event='snd', PLD=False): # Sends header and payload
        if PLD: # If segment needs to go through PLD module, use PLD's send method
            return self.PLD.send(header=header, payload=payload, event=event)
        else: # Otherwise, wrap header and payload in Segment class, serialise, send and log
            segment = Segment(header, payload)
            self.socket.send(pickle.dumps(segment))
            print('SENT! Seq num: {}'.format(header.seqNum))

            return self.logger.log(originalEvent=event, pldEvent=None, segment=segment)

    def _receive(self): # Receive and log
        response = pickle.loads(self.socket.recv(4096))
        self.logger.log(originalEvent='rcv', pldEvent=None, segment=response)

        return response

if __name__ == '__main__':
    if len(sys.argv) != 15:
        print ('Usage: python3 sender.py <receiver host> <receiver port> <filename> <maximum window size> <maximum segment size> <gamma> <drop probability> <duplicate probability> <corrupt probability> <reorder probability> <max reorder> <delay probability> <max delay time (milliseconds)> <seed>')
        sys.exit()

    # Sender arguments
    receiverHost = sys.argv[1]
    receiverPort = int(sys.argv[2])
    filename = sys.argv[3]
    mws = int(sys.argv[4])
    mss = int(sys.argv[5])
    gamma = int(sys.argv[6])
    
    #PLD module arguments
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
