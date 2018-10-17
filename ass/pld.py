import random
import sys

class PLD:
    def __init__(self, pDrop, pDuplicate, pCorrupt, pOrder, maxOrder, pDelay, maxDelay, seed):
        self.pDrop = pDrop
        self.pDuplicate = pDuplicate
        self.pCorrupt = pCorrupt
        self.pOrder = pOrder
        self.maxOrder = maxOrder
        self.pDelay = pDelay
        self.maxDelay = maxDelay
        random.seed(seed)

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
