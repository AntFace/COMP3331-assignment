import pickle
import random
import sys
import threading
import time

from helper import *

class PLD:
    def __init__(self, pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed, socket, logger):
        # Command line args
        self.pDrop = pDrop
        self.pDuplicate = pDuplicate
        self.pCorrupt = pCorrupt
        self.pOrder = pOrder
        self.maxOrder = maxOrder
        self.pDelay = pDelay
        self.maxDelay = maxDelay
        random.seed(seed)

        # Socket and logger parsed from sender to send and log appropriately
        self.socket = socket
        self.logger = logger

        # Tracks reordered segment to send after maxOrder segments
        self.reorderedSegment = None
        self.numReorderedSent = 0

        # Flag to shutdown PLD so time delayed segments do not send after sender has sent a FIN
        self.isAlive = True

    def send(self, header, payload, event):
        segment = Segment(header, payload)
        if self._checkDrop(): # Dropped segment just logs and does not call socket.send
            print('DROPPED! Seq num: {}'.format(header.seqNum))
            
            return self.logger.log(originalEvent=event, pldEvent='drop', segment=segment)
        elif self._checkDuplicate(): # Duplicated segment sends and logs first time as normal, but logs second time as a duplicate
            print('DUPLICATED! Seq num: {}'.format(header.seqNum))
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent=None, segment=segment)
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent='dup', segment=segment)

            return self._checkReorderedSegment() # Checks if reordered segment should be sent after this send - Two segments sent by duplicate are counted as one segment sent for purposes of reordering
        elif self._checkCorrupt(): # Corrupt segment gets corrupted before sending and logging
            print('CORRUPTED! Seq num: {}'.format(header.seqNum))
            segment = self._corruptSegment(segment)
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent='corr', segment=segment)

            return self._checkReorderedSegment() # Checks if reordered segment should be sent after this send
        elif self._checkReorder(): # Reordered segment
            print('REORDERING! Seq num: {}'.format(header.seqNum))

            return self._reorderSegment(segment, event)
        elif self._checkDelay(): # Delayed segment starts a delay in new thread
            print('DELAYING! Seq num: {}'.format(header.seqNum))

            thread = threading.Thread(target=self._delaySegment, args=(segment, event))
            return thread.start()
        else: # No PLD events triggered - send and log as normal
            self.socket.send(pickle.dumps(segment))
            print('SENT! Seq num: {}'.format(header.seqNum))
            self.logger.log(originalEvent=event, pldEvent=None, segment=segment)

            return self._checkReorderedSegment() # Checks if reordered segment should be sent after this one

    def shutdown(self): # Sets isAlive flag to False so time delayed segments do not send after sender has sent a FIN
        self.isAlive = False

    # All checks only generate a random number if pEvent is larger than 0
    def _checkDrop(self):
        return random.random() < self.pDrop if self.pDrop > 0 else False

    def _checkDuplicate(self):
        return random.random() < self.pDuplicate if self.pDuplicate > 0 else False

    def _checkCorrupt(self):
        return random.random() < self.pCorrupt if self.pCorrupt > 0 else False

    def _corruptSegment(self, segment): # Picks a random byte to corrupt and flips the last bit of that byte
        byteToCorrupt = random.randint(0, len(segment.payload) - 1)
        corruptPayload = segment.payload[0:byteToCorrupt] + (segment.payload[byteToCorrupt] ^ 1).to_bytes(length=1, byteorder=sys.byteorder) + segment.payload[(byteToCorrupt + 1):]
        segment.payload = corruptPayload

        return segment

    def _checkReorder(self): # If a segment is already waiting to be reordered, another segment cannot be reordered - only one segment awaiting reordering at a time
        return random.random() < self.pOrder if self.pOrder > 0 and self.reorderedSegment is None else False

    def _reorderSegment(self, segment, event): # Tracks segment to be reordered
        self.reorderedSegment = ReorderedSegment(segment=segment, event=event)

    def _checkReorderedSegment(self):
        if self.reorderedSegment is None: # If there is no segment awaiting reordering - return
            return
        else: # Increment number of segments sent
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

    def _delaySegment(self, segment, event): # To be run in new thread
        time.sleep(random.randint(0, self.maxDelay + 1) / 1000) # Sleep for [0, maxDelay] milliseconds
        if self.isAlive: # Only send after delaying if PLD is still active
            print('SENDING DELAYED! Seq num: {}'.format(segment.header.seqNum))
            self.socket.send(pickle.dumps(segment))
            self.logger.log(originalEvent=event, pldEvent='dely', segment=segment)

            return self._checkReorderedSegment() # Checks if reordered segment should be sent after this one
