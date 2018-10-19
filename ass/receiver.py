import pickle
import socket
import sys

from helper import *
from logger import *

class Receiver:
    def __init__(self, receiverPort, filename):
        # Command line args
        self.receiverPort = receiverPort
        self.filename = filename

        # State attributes
        self.state = State.CLOSED
        self.seqNum = 0
        self.ackNum = 0

        # Dict used as buffer to out of order segments
        self.buffer = {}

        # Instantiate logger
        self.logger = Logger('Receiver_log.txt')

        # Set up socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', self.receiverPort))

    def listen(self): # Listen for three-way handshake (SYN, SYN+ACK, ACK)
        print('Listening for connection...')
        self.state = State.LISTEN
        while True:
            segment, address = self._receive()
            header = segment.header
            if self.state == State.LISTEN and header.syn: # Receive SYN
                print('SYN received')
                self.state = State.SYN_RCVD
                self.ackNum += 1
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, ack=True, syn=True) # Send SYN+ACK
                self._send(address=address, header=responseHeader)
                print('Sent SYN+ACK')
            elif self.state == State.SYN_RCVD and header.ack: # Receive ACK
                print('ACK received')
                self.seqNum += 1
                self.state = State.ESTABLISHED
                print('Connection established')

                return

    def receiveFile(self): # Receive file
        while True:
            try: # Receive segment
                segment, address = self._receive()
            except TypeError: # If a corrupt or duplicate segment is received, self._receive() will return None i.e. discard the segment and continue the loop
                continue
            else: # If segment is valid
                header = segment.header
                payload = segment.payload
                print('Received segment. Segment Seq Num: {seqNum} Receiver Ack Num: {ackNum}'.format(seqNum=segment.header.seqNum, ackNum=self.ackNum))
                if header.fin: # If FIN received, begin teardown
                    return self.teardown(finAddress=address)
                elif header.seqNum == self.ackNum: # If seqNum is the next expected one, write to file
                    self._write(payload)
                    self.ackNum += len(payload)
                    while self.ackNum in self.buffer: # Check buffer for consecutive segments to write and update ackNum appropriately
                        payload = self.buffer[self.ackNum]
                        del self.buffer[self.ackNum]
                        self._write(payload)
                        self.ackNum += len(payload)
                elif header.seqNum > self.ackNum: # Out of order segment is added to buffer
                    self._addToBuffer(segment)

                print('Sending ACK. Ack Num: {}'.format(self.ackNum))
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, ack=True)
                self._send(address=address, header=responseHeader) # Send ACK

    def teardown(self, finAddress): # Four segment connection termination
        while True:
            if self.state == State.ESTABLISHED: # FIN already received in receiveFile() which calls teardown() - send ACK
                print('FIN received in receiveFile()')
                self.ackNum += 1
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, ack=True)
                self._send(address=finAddress, header=responseHeader)
                print('ACK sent')
                self.state = State.CLOSE_WAIT
            elif self.state == State.CLOSE_WAIT: # Send FIN
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, fin=True)
                self._send(address=finAddress, header=responseHeader)
                print('FIN sent')
                self.state = State.LAST_ACK
            elif self.state == State.LAST_ACK:
                segment, address = self._receive()
                header = segment.header
                if header.ack: # Receive ACK
                    self.logger.logFinal(sender=False)
                    print('ACK received')
                    self.socket.close()
                    print('Socket closed')
                    self.state == State.CLOSED
                    print('Teardown completed')

                    return

    def _send(self, address, header=None, payload=None): # Serialise, send and log segments
        segment = Segment(header=header)
        self.logger.log(originalEvent='snd', pldEvent=None, segment=segment)

        return self.socket.sendto(pickle.dumps(segment), address)

    def _receive(self): # Receive and handle segments
        segment, address = self.socket.recvfrom(4096)
        segment = pickle.loads(segment)
        # if payload exists, check if sum of checksum in header and 16-bit data in payload is 0xffff
        if segment.payload and (segment.header.checksum ^ getChecksum(segment.payload)) != 0xffff: # If checksum is off, segment is corrupt - Log and discard
            print('Corrupt segment received. Discarded!')
            self.logger.log(originalEvent='rcv', pldEvent='corr', segment=segment)

            return None # Discards segment
        if segment.header.seqNum < self.ackNum or segment.header.seqNum in self.buffer: # If received seqNum is less than ackNum or already in the buffer, segment is duplicate - Log and let receiveFile() send a dup ACK
            print('Duplicate received!')
            self.logger.log(originalEvent='rcv', pldEvent='dup', segment=segment)

            return (segment, address)

        self.logger.log(originalEvent='rcv', pldEvent=None, segment=segment) # Log properly received segment

        return (segment, address) # Returns properly received segment

    def _write(self, payload): # Writes to file
        if self.ackNum == 1: # If it's the first bit of the file, write new
            print('Writing to file...')
            with open(self.filename, 'wb') as f:
                return f.write(payload)
        else: # Otherwise append to file
            print('Appending to file...')
            with open(self.filename, 'ab') as f:
                return f.write(payload)

    def _addToBuffer(self, segment): # Add out of order payloads to buffer
        print('Adding to buffer...')
        self.buffer[segment.header.seqNum] = segment.payload

if __name__ == '__main__':
    if len(sys.argv) != 3 or not sys.argv[1].isdigit():
        sys.exit('Usage: python3 receiver.py <receiver port> <filename>')

    receiverPort = int(sys.argv[1])
    filename = sys.argv[2]

    receiver = Receiver(receiverPort, filename)
    receiver.listen()
    receiver.receiveFile()
