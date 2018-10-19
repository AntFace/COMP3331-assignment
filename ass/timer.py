import time

from collections import namedtuple

TrackedSegment = namedtuple('TrackedSegment', ['expectedACKNum', 'sendTime']) # Named tuple for currently tracked segment

class Timer:
    def __init__(self, estimatedRTT=0.5, devRTT=0.25, gamma=4):
        # Default values
        self.estimatedRTT = estimatedRTT
        self.devRTT = devRTT
        self.alpha = 0.125
        self.beta = 0.25
        self.gamma = gamma

        # Variables to calculate SampleRTTs
        self.trackedSegment = None
        self.lastSentTime = None

        # Min and max RTOs
        self.minRTO = 0.2
        self.maxRTO = 60

    @property
    def timedOut(self): # Checks if timer has timed out
        return time.time() - self.lastSentTime >= self.RTO

    @property
    def RTO(self): # Returns RTO if its between the min and max
        RTO = self.estimatedRTT + self.gamma * self.devRTT
        if RTO < self.minRTO:
            return self.minRTO
        elif RTO > self.maxRTO:
            return self.maxRTO
        else:
            return RTO

    def start(self, RXT=False, nextSeqNum=None): # Starts timer
        self.lastSentTime = time.time() # Records time to last sent segment
        if RXT: # If this segment is a retransmission, currently tracked RTT is delayed - discard it
            return self.discard()
        elif self.trackedSegment is None: # If no currently tracked segment, track this one
            print('====\n TRACKING: Seg Num: {}\n===='.format(nextSeqNum))
            self.trackedSegment = TrackedSegment(expectedACKNum=nextSeqNum, sendTime=self.lastSentTime)

    def update(self, ackNum): # Updates timer on each received ACK
        if self.trackedSegment: # If a segment is currently being tracked
            expectedACKNum = self.trackedSegment.expectedACKNum
            if ackNum == expectedACKNum: # If ACKnum is for the currently tracked segment - update RTT and then discard currently tracked segment
                self._updateRTT(time.time() - self.trackedSegment.sendTime)
                self.discard()
            elif ackNum > expectedACKNum: # ACKnum is not for currently tracked segment, then currently tracked RTT is delayed - discard it
                self.discard()

    def discard(self): # Discards currently tracked segment
        self.trackedSegment = None

    def _updateRTT(self, sampleRTT): # Updates Estimated and Dev RTTs for use in RTO calculation
        print('===\nSampleRTT: {}'.format(sampleRTT))
        self.estimatedRTT = (1 - self.alpha) * self.estimatedRTT + self.alpha * sampleRTT
        self.devRTT = (1 - self.beta) * self.devRTT + self.beta * abs(sampleRTT - self.estimatedRTT)
        print('NEW RTO: {}\n===='.format(self.RTO))
