import socket
import sys

from helper import *
from logger import *

class Receiver:
    def __init__(self, receiverPort, filename):
        self.receiverPort = receiverPort
        self.filename = filename

        self.state = State.CLOSED
        self.seqNum = 0
        self.ackNum = 0

        self.buffer = {}

        self.logger = Logger('Receiver_log.txt')

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', self.receiverPort))

    def listen(self):
        print('Listening for connection...')
        self.state = State.LISTEN
        while True:
            segment, address = self._receive()
            header = segment.header
            if self.state == State.LISTEN and header.syn:
                print('SYN received')
                self.state = State.SYN_RCVD
                self.ackNum += 1
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, ack=True, syn=True) # SYN+ACK
                self._send(address=address, header=responseHeader)
                print('Sent SYN+ACK')
            elif self.state == State.SYN_RCVD and header.ack:
                print('ACK received')
                self.seqNum += 1
                self.state = State.ESTABLISHED
                print('Connection established')

                return

    def receiveFile(self):
        while True:
            try:
                segment, address = self._receive()
            except TypeError as e:
                continue
            else:
                header = segment.header
                payload = segment.payload
                print('Received segment. Segment Seq Num: {seqNum} Receiver Ack Num: {ackNum}'.format(seqNum=segment.header.seqNum, ackNum=self.ackNum))
                if header.fin:
                    return self.teardown(finAddress=address)
                elif header.seqNum == self.ackNum:
                    self._write(payload)
                    self.ackNum += len(payload)
                    while self.ackNum in self.buffer:
                        payload = self.buffer[self.ackNum]
                        del self.buffer[self.ackNum]
                        self._write(payload)
                        self.ackNum += len(payload)
                elif header.seqNum > self.ackNum:
                    self._addToBuffer(segment)

                print('Sending ACK. Ack Num: {}'.format(self.ackNum))
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, ack=True)
                self._send(address=address, header=responseHeader)

    def teardown(self, finAddress):
        while True:
            if self.state == State.ESTABLISHED:
                print('FIN received in receiveFile()')
                self.ackNum += 1
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, ack=True)
                self._send(address=finAddress, header=responseHeader)
                print('ACK sent')
                self.state = State.CLOSE_WAIT
            elif self.state == State.CLOSE_WAIT:
                responseHeader = Header(seqNum = self.seqNum, ackNum=self.ackNum, fin=True)
                self._send(address=finAddress, header=responseHeader)
                print('FIN sent')
                self.state = State.LAST_ACK
            elif self.state == State.LAST_ACK:
                segment, address = self._receive()
                header = segment.header
                if header.ack:
                    self.logger.logFinal(sender=False)
                    print('ACK received')
                    self.socket.close()
                    print('Socket closed')
                    self.state == State.CLOSED
                    print('Teardown completed')

                    return

    def _send(self, address, header=None, payload=None):
        segment = Segment(header=header)
        self.logger.log(originalEvent='snd', pldEvent=None, segment=segment)

        return self.socket.sendto(segment.encode(), address)

    def _receive(self):
        segment, address = self.socket.recvfrom(4096)
        segment = decode(segment)
        if segment.header.seqNum < self.ackNum or segment.header.seqNum in self.buffer:
            print('Duplicate received. Discarded!')
            self.logger.log(originalEvent='rcv', pldEvent='dup', segment=segment)

            return None

        self.logger.log(originalEvent='rcv', pldEvent=None, segment=segment)

        return (segment, address)

    def _write(self, payload):
        if self.ackNum == 1:
            print('Writing to file...')
            with open(self.filename, 'wb') as f:
                return f.write(payload)
        else:
            print('Appending to file...')
            with open(self.filename, 'ab') as f:
                return f.write(payload)

    def _addToBuffer(self, segment):
        print('Adding to buffer...')
        self.buffer[segment.header.seqNum] = segment.payload

if __name__ == '__main__':
    if len(sys.argv) != 3 or not sys.argv[1].isdigit():
        sys.exit('Usage: python receiver.py <receiver port> <filename>')

    receiverPort = int(sys.argv[1])
    filename = sys.argv[2]

    receiver = Receiver(receiverPort, filename)
    receiver.listen()
    receiver.receiveFile()
