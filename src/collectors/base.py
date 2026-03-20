"""Base collector class using QThread for background data collection."""

from PySide6.QtCore import QThread


class BaseCollector(QThread):
    """Abstract base for all metric collectors.

    Subclasses implement ``collect()`` which is called on a background thread
    at the configured interval (seconds).  Errors inside ``collect()`` are
    silently swallowed so a single bad reading never crashes the application.
    """

    def __init__(self, interval: int = 1, parent=None):
        super().__init__(parent)
        self.interval = interval
        self._running = False

    def run(self):
        self._running = True
        # First tick: initialise any psutil counters that need a prior reading
        self._init()
        while self._running:
            try:
                self.collect()
            except Exception:
                pass
            self.msleep(self.interval * 1000)

    def _init(self):
        """Optional one-time initialisation before the collection loop."""

    def collect(self):
        raise NotImplementedError

    def stop(self):
        self._running = False
        self.wait(3000)
