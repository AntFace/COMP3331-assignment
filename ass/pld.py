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
        if random.random() < self.pDrop:
            return True
        
        return False
