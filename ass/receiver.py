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
            message, address = receiver.receive()
            header = decode(message).header
            if self.state == State.LISTEN and header.syn:
                self.state = State.SYN_RCVD
                self.ackNum = 1
                responseHeader = Header(ackNum=self.ackNum, ack=True, syn=True) # SYN+ACK
                receiver.send(address=address, header=responseHeader)
                print('Sent SYN+ACK')
            elif self.state == State.SYN_RCVD and header.ack:
                self.state = State.ESTABLISHED
                print('Connection established')

                return

    def receiveFile(self):
        while True:
            message, address = receiver.receive()
            message = decode(message)
            header = message.header
            print('Received message. Message Seq Num: {seqNum} Receiver Ack Num: {ackNum}'.format(seqNum=message.header.seqNum, ackNum=receiver.ackNum))
            if header.seqNum == self.ackNum:
                self.write(message.payload)
                responseHeader = Header(ackNum=self.ackNum, ack=True)
            elif header.seqNum > self.ackNum:
                self.addToBuffer(message)
                responseHeader = Header(ackNum=self.ackNum, ack=True)
            elif header.fin:
                self.teardown()

            receiver.send(address=address, header=responseHeader)

    def teardown(self):
        while True:
            if self.state == State.ESTABLISHED:
                print('FIN received in receiveFile(). Send ACK')
                self.state = State.CLOSE_WAIT
            elif self.state == State.CLOSE_WAIT:
                print('Send FIN')
                self.state = State.LAST_ACK
            elif self.state == State.LAST_ACK:
                print('Receive ACK. Send nothing.')
                self.state == State.CLOSED

                print('Teardown completed')
                return


    def receive(self):
        return self.socket.recvfrom(4096)

    def send(self, address, header=None, payload=None):
        if not header:
            return
        if payload:
            header = Header(ackNum=self.ackNum)
            message = Message(header, payload)
        else:
            message = Message(header=header)

        self.socket.sendto(message.encode(), address)

    def write(self, payload):
        print('Writing to file...')
        if self.ackNum == 1:
            with open(self.filename, 'w') as f:
                f.write(payload)
        else:
            with open(self.filename, 'a') as f:
                f.write(payload)
        self.ackNum += len(payload)

    def addToBuffer(self, message):
        print('Adding to buffer...')

if __name__ == '__main__':
    if len(sys.argv) != 3 or not sys.argv[1].isdigit():
        sys.exit('Usage: python receiver.py <receiver port> <filename>')

    receiverPort = int(sys.argv[1])
    filename = sys.argv[2]

    receiver = Receiver(receiverPort, filename)
    receiver.listen()
    receiver.receiveFile()
