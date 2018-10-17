import pickle
import random
import sys
import threading
import time

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

        self.reorderedSegment = None
        self.numReorderedSent = 0

        self.isAlive = True

    def send(self, header, payload, event):
        segment = Segment(header, payload)
        if self._checkDrop():
            print('DROPPED! Seq num: {}'.format(header.seqNum))
            
            return self.logger.log(originalEvent=event, pldEvent='drop', segment=segment)
        elif self._checkDuplicate():
            print('DUPLICATED! Seq num: {}'.format(header.seqNum))
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent=None, segment=segment)
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent='dup', segment=segment)

            return self._checkReorderedSegment()
        elif self._checkCorrupt():
            print('CORRUPTED! Seq num: {}'.format(header.seqNum))
            segment = self._corruptSegment(segment)
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent='corr', segment=segment)

            return self._checkReorderedSegment()
        elif self._checkReorder():
            print('REORDERING! Seq num: {}'.format(header.seqNum))

            return self._reorderSegment(segment, event)
        elif self._checkDelay():
            print('DELAYING! Seq num: {}'.format(header.seqNum))

            thread = threading.Thread(target=self._delaySegment, args=(segment, event))
            return thread.start()
        else:
            self.socket.send(pickle.dumps(segment))
            print('SENT! Seq num: {}'.format(header.seqNum))
            self.logger.log(originalEvent=event, pldEvent=None, segment=segment)

            return self._checkReorderedSegment()

    def shutdown(self):
        self.isAlive = False

    def _checkDrop(self):
        return random.random() < self.pDrop if self.pDrop > 0 else False

    def _checkDuplicate(self):
        return random.random() < self.pDuplicate if self.pDuplicate > 0 else False

    def _checkCorrupt(self):
        return random.random() < self.pCorrupt if self.pCorrupt > 0 else False

    def _corruptSegment(self, segment):
        byteToCorrupt = random.randint(0, len(segment.payload) - 1)
        corruptPayload = segment.payload[0:byteToCorrupt] + (segment.payload[byteToCorrupt] ^ 1).to_bytes(length=1, byteorder=sys.byteorder) + segment.payload[(byteToCorrupt + 1):]
        segment.payload = corruptPayload

        return segment

    def _checkReorder(self):
        return random.random() < self.pOrder if self.pOrder > 0 and self.reorderedSegment is None else False

    def _reorderSegment(self, segment, event):
        self.reorderedSegment = (segment, event)

    def _checkReorderedSegment(self):
        if self.reorderedSegment is None:
            return
        else:
            self.numReorderedSent += 1
            if self.numReorderedSent == self.maxOrder:
                segment = self.reorderedSegment[0]
                event = self.reorderedSegment[1]
                print('SENDING REORDERED! Seq num: {}'.format(segment.header.seqNum))
                self.socket.send(pickle.dumps(segment))
                self.reorderedSegment = None
                self.numReorderedSent = 0

                return self.logger.log(originalEvent=event, pldEvent='rord', segment=segment)

    def _checkDelay(self):
        return random.random() < self.pDelay if self.pDelay > 0 else False

    def _delaySegment(self, segment, event):
        time.sleep(random.randint(0, self.maxDelay + 1) / 1000)
        if self.isAlive:
            print('SENDING DELAYED! Seq num: {}'.format(segment.header.seqNum))
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent='dely', segment=segment)

            return self._checkReorderedSegment()
