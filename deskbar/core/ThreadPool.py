import Queue
import threading

class ThreadPool(object):
    """
    Implements a thread pool
    
    This class is used to query each module
    """

    max = 20
    started = False # Whether the pool has been started
    name = None
    workers = 0 # Number of worker threads (they pickup functions from the queue)

    def __init__(self, maxthreads=20, name=None):
        """Create a new threadpool.

        @param maxthreads: maximum number of threads in the pool
        """
        self.q = Queue.Queue(0)
        self.max = maxthreads
        self.name = name
        
        self.threads = []
        self.working = []
        
    def start(self):
        """Start the threadpool.
        """
        self.started = True
        # Start some threads.
        self.adjustPoolsize()

    def startAWorker(self):
        self.workers = self.workers + 1
        name = "PoolThread-%s" % (self.name or self.workers)
        try:
            firstJob = self.q.get(0)
        except Queue.Empty:
            return
        newThread = threading.Thread(target=self._worker, name=name, args=(firstJob,))
        self.threads.append(newThread)
        newThread.start()

    def _startSomeWorkers(self):
        while (
            self.workers < self.max and # Don't create too many
            self.q.qsize() > 0
            ):
            self.startAWorker()

    def callInThread(self, func, *args, **kw):
        o = (func, args, kw)
        self.q.put(o)
        if self.started:
            self._startSomeWorkers()

    def _worker(self, o):
        ct = threading.currentThread()
        
        while True:
            if o is not None:
                self.working.append(ct)
                function, args, kwargs = o
                
                function(*args, **kwargs)
                
                self.working.remove(ct)
                del o, function, args, kwargs
            try:
                o = self.q.get(False) # Get new element from queue
            except Queue.Empty:
                break
        
        self.threads.remove(ct)
        self.workers = self.workers - 1

    def stop(self):
        """Shutdown the threads in the threadpool."""
        self.q = Queue.Queue(0)

    def adjustPoolsize(self, maxthreads=None):
        if maxthreads is None:
            maxthreads = self.max

        self.max = maxthreads
        if not self.started:
            return

        # Start some threads if there is a need.
        self._startSomeWorkers()

    def stats(self):
        print "Queue size: %i" % self.q.qsize()
        #print "Working: "
        #print self.working
        print "Workers: %i" % self.workers
        #print "Threads: "
        #print self.threads
