class MovingAverage:
    def __init__(self, windowSize) -> None:
        self._windowSize = windowSize
        self._historyWindow = [0] * windowSize
        self._historyIndex = 0
        self._historyCount = 0

    def recordValue(self, value):
        self._historyWindow[self._historyIndex] = value
        self._historyIndex += 1
        if self._historyIndex >= self._windowSize:
            self._historyIndex = 0
        self._historyCount += 1

    def getAverage(self):
        endIndex = self._windowSize
        if self._historyCount < self._windowSize:
            endIndex = self._historyCount
        total = 0
        if endIndex == 0:
            return 0
        for i in range(endIndex):
            total += self._historyWindow[i]
        return total / endIndex
