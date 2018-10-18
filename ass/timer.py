import time

from collections import namedtuple

TrackedSegment = namedtuple('TrackedSegment', ['expectedACKNum', 'sendTime'])

class Timer:
    def __init__(self, estimatedRTT=0.5, devRTT=0.25, gamma=4):
        self.estimatedRTT = estimatedRTT
        self.devRTT = devRTT
        self.alpha = 0.125
        self.beta = 0.25
        self.gamma = gamma

        self.trackedSegment = None
        self.lastSentTime = None

        self.minRTO = 0.2
        self.maxRTO = 60

    @property
    def timedOut(self):
        return time.time() - self.lastSentTime >= self.RTO

    @property
    def RTO(self):
        RTO = self.estimatedRTT + self.gamma * self.devRTT
        if RTO < self.minRTO:
            return self.minRTO
        elif RTO > self.maxRTO:
            return self.maxRTO
        else:
            return RTO

    def start(self, RXT=False, nextSeqNum=None):
        self.lastSentTime = time.time()
        if RXT:
            return self.discard()
        elif self.trackedSegment is None:
            print('====\n TRACKING: Seg Num: {}\n===='.format(nextSeqNum))
            self.trackedSegment = TrackedSegment(expectedACKNum=nextSeqNum, sendTime=self.lastSentTime)

    def update(self, ackNum):
        if self.trackedSegment:
            expectedACKNum = self.trackedSegment.expectedACKNum
            if ackNum == expectedACKNum:
                self._updateRTT(time.time() - self.trackedSegment.sendTime)
                self.discard()
            elif ackNum > expectedACKNum:
                self.discard()

    def discard(self):
        self.trackedSegment = None

    def _updateRTT(self, sampleRTT):
        print('===\nSampleRTT: {}'.format(sampleRTT))
        self.estimatedRTT = (1 - self.alpha) * self.estimatedRTT + self.alpha * sampleRTT
        self.devRTT = (1 - self.beta) * self.devRTT + self.beta * abs(sampleRTT - self.estimatedRTT)
        print('NEW RTO: {}\n===='.format(self.RTO))
