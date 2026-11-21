"""Short bounded primary cooldown after consecutive transport failures."""
import threading
import time
class ProviderHealth:
    def __init__(self):
        self.lock=threading.Lock()
        self.failures=0
        self.until=0.0
    def prefer_backup(self):
        with self.lock:return time.monotonic()<self.until
    def failure(self):
        with self.lock:
            self.failures+=1
            if self.failures>=2:self.until=time.monotonic()+10.0
    def success(self):
        with self.lock:self.failures=0;self.until=0.0
HEALTH=ProviderHealth()
