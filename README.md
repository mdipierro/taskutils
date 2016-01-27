# tasktuils

**taskutils** is a implements a multithreaded scheduler in Python. 
It provide methods to enqueue tasks and set simple policies, for example:

- execute once with this priority
- execute every 10 minutes
- retry twice if it fails
- execute no more than 3 tasks concurrently

It can used to power more complex programs that need concurrency, for example a crawler.

Here is an example of usage:

### Install it

    pip install taskutils

### Import the relevant objects

    from taskutils import TaskHandler, Task, Recurrent

### Create the main task handler object

    task_handler = TaskHandler(max_num_threads=3, sleep_seconds=2)

This will create 3 threads that wait for tasks to be queued every 2 seconds.

### Queue some simple tasks

    def foo(k): print 'hello world from task %s' % k

    for k in range(10):
        task = Task(foo, kwargs=dict(k=k), priority=k, repeats_on_failure=3)
        task_handler.enqueue_task(task)

This will enqueue 10 tasks (with arbitrary parameter k=0...9) which will be executed by
the task handler threads when free. If a task fails it will be retried 3 times before being 
discarded. Notice that a task contain a function (in this case foo) and its arguments.

### Queue a recurrent task

    task = Task(foo, kwargs=dict(k=10), repeats_on_failure=0)
    task_handler.recurrent_tasks['abc'] = Recurrent(task, interval=3, repeats=5)

Recurrent tasks are wrapped into the Recurrent() object and must be named (for example 'abc').
Recurrent tasks are named because they are not placed in the normal queue but are executed always 
with max priority when their time comes. In the above example the 'abc' task is executed 
5 times every 3 seconds. A recurrent task can be removed via

    del task_handler.recurrent_tasks['abc']

### Other goodies

    from taskutils import LockWrapper
    with_a_lock = LockWrapper()

It defines a decorator that makes sure all code called with the decorator is always serialized, even if called in different Tasks:

    @with_a_lock
    def f(): print 'a'
    
    @with_a_lock
    def g(): print 'b'

    task_handler.enqueue_task(Task(f))
    task_handler.enqueue_task(Task(g))

This makes sure that the excution of functions f and g is never concurrent.

## License

Created by Massimo Di Pierro (http://experts4solutions.com) @2016 BSDv3 License

