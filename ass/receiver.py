import socket
import sys
import time

from helper import *

class Receiver:
    def __init__(self, receiverPort, filename):
        self.receiverPort = receiverPort
        self.filename = filename

        self.state = State.CLOSED
        self.ackNum = 0

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', self.receiverPort))

    def listen(self):
        print('Listening for connection...')
        self.state = State.LISTEN
        while True:
            segment, address = self._receive()
            header = decode(segment).header
            if self.state == State.LISTEN and header.syn:
                print('SYN received')
                self.state = State.SYN_RCVD
                self.ackNum = 1
                responseHeader = Header(ackNum=self.ackNum, ack=True, syn=True) # SYN+ACK
                self._send(address=address, header=responseHeader)
                print('Sent SYN+ACK')
            elif self.state == State.SYN_RCVD and header.ack:
                print('ACK received')
                self.state = State.ESTABLISHED
                print('Connection established')

                return

    def receiveFile(self):
        while True:
            segment, address = self._receive()
            segment = decode(segment)
            header = segment.header
            payload = segment.payload
            print('Received segment. Segment Seq Num: {seqNum} Receiver Ack Num: {ackNum}'.format(seqNum=segment.header.seqNum, ackNum=self.ackNum))
            if header.fin:
                return self.teardown(finAddress=address)
            elif header.seqNum == self.ackNum:
                self._write(payload)
                self.ackNum += len(payload)
                responseHeader = Header(ackNum=self.ackNum, ack=True)
            elif header.seqNum > self.ackNum:
                self._addToBuffer(segment)
                responseHeader = Header(ackNum=self.ackNum, ack=True)

            self._send(address=address, header=responseHeader)

    def teardown(self, finAddress):
        while True:
            if self.state == State.ESTABLISHED:
                print('FIN received in receiveFile()')
                self.ackNum += 1
                responseHeader = Header(ackNum=self.ackNum, ack=True)
                self._send(address=finAddress, header=responseHeader)
                print('ACK sent')
                self.state = State.CLOSE_WAIT
            elif self.state == State.CLOSE_WAIT:
                responseHeader = Header(ackNum=self.ackNum, fin=True)
                self._send(address=finAddress, header=responseHeader)
                print('FIN sent')
                self.state = State.LAST_ACK
            elif self.state == State.LAST_ACK:
                segment, address = self._receive()
                header = decode(segment).header
                if header.ack:
                    print('ACK received')
                    self.socket.close()
                    print('Socket closed')
                    self.state == State.CLOSED
                    print('Teardown completed')

                return


    def _receive(self):
        return self.socket.recvfrom(4096)

    def _send(self, address, header=None, payload=None):
        segment = Segment(header=header)

        return self.socket.sendto(segment.encode(), address)

    def _write(self, payload):
        if self.ackNum == 1:
            print('Writing to file...')
            with open(self.filename, 'w') as f:
                return f.write(payload)
        else:
            print('Appending to file...')
            with open(self.filename, 'a') as f:
                return f.write(payload)

    def _addToBuffer(self, segment):
        print('Adding to buffer...')

if __name__ == '__main__':
    if len(sys.argv) != 3 or not sys.argv[1].isdigit():
        sys.exit('Usage: python receiver.py <receiver port> <filename>')

    receiverPort = int(sys.argv[1])
    filename = sys.argv[2]

    receiver = Receiver(receiverPort, filename)
    receiver.listen()
    receiver.receiveFile()
