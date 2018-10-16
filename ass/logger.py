import time

class Logger:
    def __init__(self, filename):
        self.filename = filename
        self.startTime = time.time()

        # Sender Final Statistics
        self.sentFilesize = 0
        self.segmentsTransmitted = 0
        self.segmentsHandledByPLD = 0
        self.segmentsDropped = 0
        self.segmentsCorrupted = 0
        self.segmentsReordered = 0
        self.segmentsDuplicated = 0
        self.segmentsDelayed = 0
        self.timeoutRetransmissions = 0
        self.fastRetransmissions = 0
        self.dupACKsReceived = 0

        # Receiver Final Statistics
        self.receivedFilesize = 0
        self.totalSegmentsReceived = 0
        self.dataSegmentsReceived = 0
        self.bitErrorsReceived = 0
        self.duplicatesReceived = 0
        self.dupACKsSent = 0
        

    def log(self, event, segment):
        # Update final statistics
        if event == 'snd':
            self.segmentsTransmitted += 1
            if segment.payload:
                self.sentFilesize += len(segment.payload)
        elif event == 'rcv':
            self.totalSegmentsReceived += 1
            if segment.payload:
                self.dataSegmentsReceived += 1
                self.receivedFilesize += len(segment.payload)
        elif event == 'drop':
            self.segmentsTransmitted += 1
            self.segmentsDropped += 1

        # Calculate time
        logTime = time.time() - self.startTime

        # Generate packetType
        if segment.payload:
            packetType = 'D'
            self.segmentsHandledByPLD += 1
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
        logString = '{0:<10} {1:>10.2f} {2:^10} {3:>10} {4:>10} {5:>10}\n'.format(event, logTime, packetType, seqNum, payloadLength, ackNum)

        if seqNum == 0 and ackNum == 0:
            with open(self.filename, 'w') as f:
                return f.write(logString)
        else:
            with open(self.filename, 'a') as f:
                return f.write(logString)

    def logFinal(self, sender=True):
        if sender:
            final = '{0:<50} {1:>10}\n'.format('Size of the File (in Bytes)', self.sentFilesize)
            final += '{0:<50} {1:>10}\n'.format('Segments Transmitted (including drop & RXT)', self.segmentsTransmitted)
            final += '{0:<50} {1:>10}\n'.format('Number of Segments Handled by PLD', self.segmentsHandledByPLD)
            final += '{0:<50} {1:>10}\n'.format('Number of Segments Dropped', self.segmentsDropped)
            final += '{0:<50} {1:>10}\n'.format('Number of Segments Corrupted', self.segmentsCorrupted)
            final += '{0:<50} {1:>10}\n'.format('Number of Segments Re-ordered', self.segmentsReordered)
            final += '{0:<50} {1:>10}\n'.format('Number of Segments Duplicated', self.segmentsDuplicated)
            final += '{0:<50} {1:>10}\n'.format('Number of Segments Delayed', self.segmentsDelayed)
            final += '{0:<50} {1:>10}\n'.format('Number of Retransmissions due to Timeout', self.timeoutRetransmissions)
            final += '{0:<50} {1:>10}\n'.format('Number of Fast Retransmissions', self.fastRetransmissions)
            final += '{0:<50} {1:>10}\n'.format('Number of Duplicate ACKs received', self.dupACKsReceived)
        else:
            final = '{0:<50} {1:>10}\n'.format('Amount of Data Received (in Bytes)', self.receivedFilesize)
            final += '{0:<50} {1:>10}\n'.format('Total Segments Received', self.totalSegmentsReceived)
            final += '{0:<50} {1:>10}\n'.format('Data Segments Received', self.dataSegmentsReceived)
            final += '{0:<50} {1:>10}\n'.format('Data Segments with Bit Errors', self.bitErrorsReceived)
            final += '{0:<50} {1:>10}\n'.format('Duplicate Data Segments Received', self.duplicatesReceived)
            final += '{0:<50} {1:>10}\n'.format('Duplicate ACKs sent', self.dupACKsSent)
        final = '\n===== Final Statistics =====\n' + final
        with open(self.filename, 'a') as f:
            return f.write(final)
