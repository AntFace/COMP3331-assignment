import random

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
