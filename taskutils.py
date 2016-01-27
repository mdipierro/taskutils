# Created by Massimo Di Pierro @ 2016, BSD v3 License
import time
import threading
import traceback
import thread
import collections
from functools import wraps

class LockWrapper(object):
    def __init__(self, lock=None):
        self.lock = lock or threading.Lock()
    def __call__(self, func):
        @wraps(func)
        def wrapper(*a, **b):
            try:
                self.lock.acquire()
                return func(*a, **b)
            finally:
                self.lock.release()
        return wrapper
        
with_tasks_queue_lock = LockWrapper()

class FileWrapper(object):
    def __init__(self, filename):
        self.filename = filename    

class WorkerThread(threading.Thread):
    """
    The plan is to for the server to create a fixed number of worker threads which
    will loop and pick tasks from Handler.tasks_queue. If no tasks it waits
    this will prevent a proliferation of tasks. If a task fails and does not causes the thread 
    to crash it is reinjected in the queue with failures++.
    if it fails the thread to crash, the thread is re-created by the Handler
    """
    def __init__(self, handler):
        threading.Thread.__init__(self)
        self.handler = handler
    def run(self):
        while True:
            if not self.handler.paused:
                self.handler.heartbeats[thread.get_ident()] = time.time()
                task = self.handler.get_next_task()
            if not self.handler.paused and task:
                try:
                    print 'executing task'
                    task.execute()
                    if task.logger: task.logger.info('completed')
                except:
                    exc = traceback.format_exc()
                    print exc
                    if task.logger: task.logger.warn('task error:\n%s' % exc)
                    task.failures += 1
                    if task.resubmit_on_failure and task.failures < self.repeats_on_failure:
                        self.handler.enqueue_task(task)          
                        if task.logger: task.logger.info('resubmitted')
            else:
                time.sleep(self.handler.sleep_seconds)

class Task(object):
    """
    a task is a function (func) and a set of arguments, this class wraps that function.
    a task has a priority which determines its location in the tasks_queue
    highest priority means earlier, tasks with the same priority are inserted in time order
    """
    def __init__(self, func, args=(), kwargs={}, priority=0, repeats_on_failure=1, logger=None):
        self.priority = priority
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.repeats_on_failure = repeats_on_failure
        self.failures = 0
        self.logger = logger

    def execute(self):        
        self.func(*self.args, **self.kwargs)        

class Recurrent(object):
    def __init__(self, task, interval, repeats=1, start=None, stop=None,):
        self.task = task
        self.start = start or time.time() # datetime
        self.stop = stop # datetime
        self.repeats = repeats # integer
        self.interval = interval # seconds
        self.last_run = None
        self.repeated = 0

    def is_ready(self):
        now = time.time()
        if ((self.start < now) and
            (not self.stop or now < self.stop) and
            (not self.repeats or self.repeated < self.repeats) and
            (not self.last_run or now - self.last_run > self.interval)):
            return True

class TaskHandler(object):
    """
    tha main client obect
    """
    def __init__(self, max_num_threads=3, sleep_seconds=1):
        self.tasks_queue = []
        self.tasks_failed = []
        self.tasks_completed = []
        self.task_completed = []
        self.max_num_threads = max_num_threads
        self.running_threads = []
        self.sleep_seconds = sleep_seconds 
        self.paused = False
        self.recurrent_tasks = collections.OrderedDict()
        self.heartbeats = {} # this allows to check if threads got stuck but there is nothing to handle it yet
        self.restart_threads()       
   
    def restart_threads(self):
        """ make sure there are max_num_threads running threads - DO NOT LOCK THIS"""
        while len(self.running_threads) < self.max_num_threads:
            mythread = WorkerThread(self)
            mythread.start()
            self.running_threads.append(mythread)

    @with_tasks_queue_lock
    def enqueue_task(self, task):
        """ 
        enqueus a new task, also checks and restarts threads that may have died
        """
        self.restart_threads()
        for k, other in enumerate(self.tasks_queue):
            if other.priority < task.priority:
                self.tasks_queue.insert(k, task)
                break
        else:
            self.tasks_queue.append(task)

    @with_tasks_queue_lock
    def get_next_task(self):
        """
        retrieves the next task to be processed
        """
        for recurrent_task in self.recurrent_tasks.itervalues():
            if recurrent_task.is_ready():
                recurrent_task.last_run = time.time()
                recurrent_task.repeated += 1
                return recurrent_task.task
            
        return self.tasks_queue.pop() if self.tasks_queue else None

    def pause(self):
        self.paused = True
        
    def resume(self):
        self.paused = False

def main_example():
    # create a function that will be wrapped in a task and executed periodically
    def dummy_task(k):
        print 'hello world from task %s' % k
        time.sleep(2)
    # create a task handler that will allow to enqueue and execute tasks
    task_handler = TaskHandler(max_num_threads=3, sleep_seconds=1)
    # enque 10 tasks: dummy_task(0), dummy_task(1), dummy_task(2), with prioriy 10-k
    # when a task files, it is retried
    for k in range(10):
        task = Task(dummy_task, args=(k,), priority=10-k, repeats_on_failure=3)
        task_handler.enqueue_task(task)
    # every 3 seconds, up to five time, run recurrent task dummy_task(-1)
    # priotiy of recurrent tasks is ignored since they are executed when due (more or less)
    # when a repeated task fails it is only retried when due next
    task = Task(dummy_task, args=(-1,), repeats_on_failure=0)
    task_handler.recurrent_tasks['try this'] = Recurrent(task, interval=3, repeats=5)
    # wait and enqueue one more task
    time.sleep(12)    
    task_handler.enqueue_task(Task(dummy_task, args=(10,), priority=19))

if __name__ == '__main__':
    main_example()

