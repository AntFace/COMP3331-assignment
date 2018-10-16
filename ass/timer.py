import time

class Timer:
    def __init__(self, estimatedRTT=0.5, devRTT=0.25, gamma=4):
        self.estimatedRTT = estimatedRTT
        self.devRTT = devRTT
        self.alpha = 0.125
        self.beta = 0.25
        self.gamma = gamma

        self.startTime = None

    @property
    def isRunning(self):
        return self.startTime is not None

    def start(self):
        self.startTime = time.time()

    def stop(self):
        self._update(time.time() - self.startTime)
        self.startTime = None

    def discard(self):
        self.startTime = None

    def getTimeoutInterval(self):
        return self.estimatedRTT + self.gamma * self.devRTT

    def _update(self, sampleRTT):
        self.estimatedRTT = (1 - self.alpha) * self.estimatedRTT + self.alpha * self.estimatedRTT
        self.devRTT = (1 - self.beta) * self.devRTT + self.beta * abs(sampleRTT - self.estimatedRTT)
