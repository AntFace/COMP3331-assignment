import time

class Logger:
    def __init__(self, filename):
        self.filename = filename
        self.startTime = None

    def log(self, event, segment):
        # Calculate time
        if not self.startTime:
            self.startTime = currentTime = time.time()
        else:
            currentTime = time.time()
        logTime = currentTime - self.startTime

        # Generate packetType
        if segment.payload:
            packetType = 'D'
        elif segment.header.syn and segment.header.ack:
            packetType = 'SA'
        elif segment.header.syn:
            packetType = 'S'
        elif segment.header.ack:
            packetType = 'A'
        elif segment.header.fin:
            packetType = 'F'
        else:
            packetType = 'N/A'

        # Sequence number
        seqNum = segment.header.seqNum

        # Number of bytes in data
        if segment.payload:
            payloadLength = len(segment.payload)
        else:
            payloadLength = 0

        # Acknowledgement number
        ackNum = segment.header.ackNum

        # Generate log string
        logString = '{0:<10}{1:<10.2f}{2:<10}{3:<10}{4:<10}{5}\n'.format(event, logTime, packetType, seqNum, payloadLength, ackNum)

        if logTime == 0:
            with open(self.filename, 'w') as f:
                return f.write(logString)
        else:
            with open(self.filename, 'a') as f:
                return f.write(logString)
