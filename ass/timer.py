class Timer:
    def __init__(self, timeout=1, estimatedRTT=0, devRTT=0, gamma):
        self.timeout = timeout
        self.estimatedRTT = estimatedRTT
        self.devRTT = devRTT
        self.alpha = 0.125
        self.beta = 0.25
        self.gamma = gamma
