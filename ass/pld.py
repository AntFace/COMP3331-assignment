import pickle
import random
import sys

from helper import *

class PLD:
    def __init__(self, pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed, socket, logger):
        self.pDrop = pDrop
        self.pDuplicate = pDuplicate
        self.pCorrupt = pCorrupt
        self.pOrder = pOrder
        self.maxOrder = maxOrder
        self.pDelay = pDelay
        self.maxDelay = maxDelay
        random.seed(seed)

        self.socket = socket
        self.logger = logger

    def send(self, header, payload, event):
        segment = Segment(header, payload)
        if self.checkDrop():
            print('DROPPED! Seq num: {}'.format(header.seqNum))
            
            return self.logger.log(originalEvent=event, pldEvent='drop', segment=segment)
        elif self.checkDuplicate():
            print('DUPLICATED! Seq num: {}'.format(header.seqNum))
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent=None, segment=segment)
            self.socket.send(pickle.dumps(segment))

            return self.logger.log(originalEvent=event, pldEvent='dup', segment=segment)
        elif self.checkCorrupt():
            print('CORRUPTED! Seq num: {}'.format(header.seqNum))
            segment = self.corruptSegment(segment)
            self.socket.send(pickle.dumps(segment))

            return self.logger.log(originalEvent=event, pldEvent='corr', segment=segment)
        else:
            self.socket.send(pickle.dumps(segment))
            print('SENT! Seq num: {}'.format(header.seqNum))

            return self.logger.log(originalEvent=event, pldEvent=None, segment=segment)

    def checkDrop(self):
        return True if random.random() < self.pDrop else False

    def checkDuplicate(self):
        return True if random.random() < self.pDuplicate else False

    def checkCorrupt(self):
        return True if random.random() < self.pCorrupt else False

    def corruptSegment(self, segment):
        byteToCorrupt = random.randint(0, len(segment.payload) - 1)
        corruptPayload = segment.payload[0:byteToCorrupt] + (segment.payload[byteToCorrupt] ^ 1).to_bytes(length=1, byteorder=sys.byteorder) + segment.payload[(byteToCorrupt + 1):]
        segment.payload = corruptPayload

        return segment
