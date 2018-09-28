import socket
import sys
import time

from helper import *

class Receiver:
    def __init__(self, receiverPort, filename):
        self.receiverPort = receiverPort
        self.filename = filename

        self.ackNum = 0

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('localhost', self.receiverPort))

    def receive(self):
        return self.socket.recvfrom(4096)

    def send(self, address, header=None, payload=None):
        if payload:
            header = Header(0, self.ackNum)
            message = Message(header, payload)
        else:
            message = Message(header=header)

        self.socket.sendto(message.encode(), address)

if __name__ == '__main__':
    if len(sys.argv) != 3 or not sys.argv[1].isdigit():
        sys.exit('Usage: python receiver.py <receiver port> <filename>')

    receiverPort = int(sys.argv[1])
    filename = sys.argv[2]

    receiver = Receiver(receiverPort, filename)

    size = 0
    while True:
        message, address = receiver.receive()
        size += 1
        if message:
            header = decode(message).header
            if header.syn:
                receiver.ackNum = header.seqNum + 1
                responseHeader = Header(0, receiver.ackNum, 0, 0, 0, 0, 1, 1, 0) # SYN+ACK
                receiver.send(address=address, header=responseHeader)
                print('Sent SYN+ACK')
            elif header.ack:
                receiver.ackNum = header.seqNum + 1
                responseHeader = Header(0, receiver.ackNum)
                print('Connection established')
