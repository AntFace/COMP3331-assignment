class Timer:
    def __init__(self, estimatedRTT=0.5, devRTT=0.25, gamma=4):
        self.estimatedRTT = estimatedRTT
        self.devRTT = devRTT
        self.alpha = 0.125
        self.beta = 0.25
        self.gamma = gamma

    def getTimeoutInterval(self):
        return self.estimatedRTT + self.gamma * self.devRTT
