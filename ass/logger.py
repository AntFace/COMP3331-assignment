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

        # Receiver Final Statistics
        self.receivedFilesize = 0
        self.totalSegmentsReceived = 0
        self.dataSegmentsReceived = 0
        self.bitErrorsReceived = 0
        self.duplicatesReceived = 0

        # Shared Final Statistics
        self.duplicateACKs = 0

        # Keeps track of previous ACKs to detect duplicates
        self.previousACKs = set()

    def log(self, originalEvent, pldEvent, segment):
        # Generate event and calculate/correct final statistics
        sendEvents = ['snd', 'timeoutRXT', 'fastRXT']
        if originalEvent == 'snd':
            event = originalEvent
            self.segmentsTransmitted += 1
            if segment.payload:
                self.segmentsHandledByPLD += 1
                self.sentFilesize += len(segment.payload)
        elif originalEvent == 'timeoutRXT':
            event = 'snd/RXT'
            self.segmentsTransmitted += 1
            self.segmentsHandledByPLD += 1
            self.timeoutRetransmissions += 1
            self.sentFilesize += len(segment.payload)
        elif originalEvent == 'fastRXT':
            event = 'snd/RXT'
            self.segmentsTransmitted += 1
            self.segmentsHandledByPLD += 1
            self.fastRetransmissions += 1
            self.sentFilesize += len(segment.payload)
        elif originalEvent == 'rcv':
            event = originalEvent
            self.totalSegmentsReceived += 1
            if segment.payload:
                self.dataSegmentsReceived += 1
                self.receivedFilesize += len(segment.payload)

        if pldEvent == 'drop':
            event = event.replace('snd', 'drop')
            self.segmentsDropped += 1
            self.sentFilesize -= len(segment.payload)
        elif pldEvent == 'dup':
            event += '/dup'
            if originalEvent in sendEvents:
                self.segmentsDuplicated += 1
                self.sentFilesize -= len(segment.payload)
                if originalEvent == 'timeoutRXT':
                    self.timeoutRetransmissions -= 1
                elif originalEvent == 'fastRXT':
                    self.fastRetransmissions -= 1
            else:
                self.duplicatesReceived += 1
                self.receivedFilesize -= len(segment.payload)
        elif pldEvent == 'corr':
            event += '/corr'
            if originalEvent in sendEvents:
                self.segmentsCorrupted += 1
                self.sentFilesize -= len(segment.payload)
            else:
                self.bitErrorsReceived += 1
                self.receivedFilesize -= len(segment.payload)
        elif pldEvent == 'rord':
            event += '/rord'
            self.segmentsReordered += 1
        elif pldEvent == 'dely':
            event += '/dely'
            self.segmentsDelayed += 1


        # Calculate time
        logTime = time.time() - self.startTime

        # Generate packetType
        if segment.payload:
            packetType = 'D'
        elif segment.header.syn and segment.header.ack:
            packetType = 'SA'
        elif segment.header.syn:
            packetType = 'S'
        elif segment.header.ack:
            packetType = 'A'
            if segment.header.ackNum in self.previousACKs:
                self.duplicateACKs += 1
                event += '/DA'
            else:
                self.previousACKs.add(segment.header.ackNum)
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
        logString = '{0:<20} {1:>10.2f} {2:^10} {3:>10} {4:>10} {5:>10}\n'.format(event, logTime, packetType, seqNum, payloadLength, ackNum)

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
            final += '{0:<50} {1:>10}\n'.format('Number of Duplicate ACKs received', self.duplicateACKs)
        else:
            final = '{0:<50} {1:>10}\n'.format('Amount of Data Received (in Bytes)', self.receivedFilesize)
            final += '{0:<50} {1:>10}\n'.format('Total Segments Received', self.totalSegmentsReceived)
            final += '{0:<50} {1:>10}\n'.format('Data Segments Received', self.dataSegmentsReceived)
            final += '{0:<50} {1:>10}\n'.format('Data Segments with Bit Errors', self.bitErrorsReceived)
            final += '{0:<50} {1:>10}\n'.format('Duplicate Data Segments Received', self.duplicatesReceived)
            final += '{0:<50} {1:>10}\n'.format('Duplicate ACKs sent', self.duplicateACKs)
        final = '\n===== Final Statistics =====\n' + final
        with open(self.filename, 'a') as f:
            return f.write(final)
