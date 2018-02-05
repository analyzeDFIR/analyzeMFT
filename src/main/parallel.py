# -*- coding: UTF-8 -*-
# parallel.py
# Noah Rubin
# 02/05/2018

from multiprocessing import Process, JoinableQueue, cpu_count

class QueueWorker(Process):
    '''
    Class to spawn worker process with queue of tasks
    '''
    def __init__(self, queue, *args, **kwargs):
        super(QueueWorker, self).__init__()
        self._queue = queue
        self._args = args
        self._kwargs = kwargs
    def run(self):
        '''
        Args:
            N/A
        Procedure:
            Run the worker, picking tasks off the queue until 
            a poison pill is encountered
        Preconditions:
            N/A
        '''
        while True:
            task = self._queue.get()
            self._queue.task_done()
            if task is None:
                break
            try:
                task(*args, **kwargs)
            except Exception as e:
                #TODO: implement logging for errors encountered here
                pass

class WorkerPool(object):
    '''
    Class to manage pool of QueueWorker instances
    '''
    def __init__(self, task_queue, *args, daemonize=True, worker_count=(2 if cpu_count() <= 4 else 4), **kwargs):
        self._worker_class = QueueWorker
        self._task_queue = task_queue
        self._task_args = args
        self._task_kwargs = kwargs
        self._workers = None
        self.daemon = daemonize
        self.worker_count = worker_count
    def add_task(self, task):
        '''
        Args:
            N/A
        Procedure:
            Add task to task queue
        Preconditions:
            N/A
        '''
        if hasattr(self._queue, 'put_nowait'):
            self._queue.put_nowait(task)
        else:
            self._queue.put(task)
    def add_poison_pills(self):
        '''
        Args:
            N/A
        Procedure:
            Add poison pill to task queue
        Preconditions:
            N/A
        '''
        for i in range(self.worker_count):
            self.add_task(None)
    def start(self):
        '''
        Args:
            N/A
        Procedure:
            Start all worker objects in self._workers
        Preconditions:
            N/A
        '''
        if self._workers is None:
            self._workers = [\
                QueueWorker(self._task_queue, *args, **kwargs)\
                for i in range(self.worker_count)\
            ]
        for worker in self._workers:
            if not worker.is_alive():
                worker.daemon = self.daemon
                worker.start()
        return True
    def join_tasks(self):
        '''
        Args:
            N/A
        Procedure:
            Join on self._queue if is of type JoinableQueue
        Preconditions:
            N/A
        '''
        if isinstance(self._queue, JoinableQueue):
            self._queue.join()
        return True
    def join_workers(self):
        '''
        Args:
            N/A
        Procedure:
            Join all living worker processes in self._workers
        Preconditions:
            N/A
        '''
        if self._workers is not None:
            map(lambda x: x.join(), [worker for worker in self._workers if worker.is_alive()])
        return True
    def terminate(self):
        '''
        Args:
            N/A
        Procedure:
            Terminate all living worker processes in self._workers
        Preconditions:
            N/A
        '''
        if self._workers is not None:
            for worker in self._workers:
                if worker.is_alive():
                    worker.terminate()
