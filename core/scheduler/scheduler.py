import logging
import threading
import time
import datetime
import heapq
from typing import Callable, Dict, Tuple
from ..common.exceptions import SchedulerError

logger = logging.getLogger(__name__)

class Task:
    """Represents a scheduled task to be executed."""
    
    def __init__(self, 
                 task_id: str, 
                 execute_at: datetime.datetime, 
                 callback: Callable, 
                 args: Tuple = None, 
                 kwargs: Dict = None):
        self.task_id = task_id
        self.execute_at = execute_at
        self.callback = callback
        self.args = args or ()
        self.kwargs = kwargs or {}
        
    def __lt__(self, other):
        return self.execute_at < other.execute_at
        
    def execute(self):
        try:
            return self.callback(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(
                "task_execution_failed",
                extra={
                    "task_id": self.task_id,
                    "error": str(e)
                }
            )
            raise


class TaskScheduler:
    """Scheduler for managing and executing background tasks."""
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance of TaskScheduler."""
        if cls._instance is None:
            cls._instance = TaskScheduler()
        return cls._instance
    
    def __init__(self):
        self.tasks = []
        self.tasks_by_id = {}
        self.lock = threading.RLock()
        self.running = False
        self.scheduler_thread = None
        
    def schedule_task(self, 
                     task_id: str, 
                     execute_at: datetime.datetime, 
                     callback: Callable, 
                     *args, 
                     **kwargs) -> Task:
        """
        Schedule a new task to run at a specific time.
        
        Raises:
            SchedulerError: If a task with the same ID already exists
        """
        with self.lock:
            if task_id in self.tasks_by_id:
                raise SchedulerError(f"Task with ID {task_id} already scheduled")
                
            task = Task(task_id, execute_at, callback, args, kwargs)
            heapq.heappush(self.tasks, task)
            self.tasks_by_id[task_id] = task
            
            logger.info(
                "task_scheduled",
                extra={
                    "task_id": task_id,
                    "execute_at": execute_at.isoformat()
                }
            )
            
            return task
    
    def schedule_match_start(self, match_id: int, execute_at: datetime.datetime,
                           match_service_factory: Callable) -> Task:
        """Schedule a match to start at the specified time."""
        task_id = f"match_start_{match_id}_{execute_at.timestamp()}"
        
        def start_match_task():
            try:
                match_service = match_service_factory()
                return match_service.start_match(match_id)
            except Exception as e:
                logger.error(
                    "scheduled_match_start_failed",
                    extra={
                        "match_id": match_id,
                        "error": str(e)
                    }
                )
                return False
        
        return self.schedule_task(task_id, execute_at, start_match_task)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task by ID. Returns True if found and canceled."""
        with self.lock:
            if task_id in self.tasks_by_id:
                task = self.tasks_by_id.pop(task_id)
                
                logger.info(
                    "task_canceled",
                    extra={
                        "task_id": task_id,
                        "was_scheduled_for": task.execute_at.isoformat()
                    }
                )
                
                return True
            return False
    
    def start(self):
        if self.running:
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="TaskScheduler"
        )
        self.scheduler_thread.start()
        
        logger.info("scheduler_started")
    
    def stop(self):
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
            self.scheduler_thread = None
            
        logger.info("scheduler_stopped")
    
    def _scheduler_loop(self):
        while self.running:
            try:
                self._process_due_tasks()
                time.sleep(1.0)
            except Exception as e:
                logger.error(
                    "scheduler_loop_error",
                    extra={"error": str(e)}
                )
    
    def _process_due_tasks(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        
        with self.lock:
            while self.tasks and self.tasks[0].execute_at <= now:
                task = heapq.heappop(self.tasks)
                
                if task.task_id not in self.tasks_by_id:
                    continue
                    
                del self.tasks_by_id[task.task_id]
                
                threading.Thread(
                    target=self._execute_task,
                    args=(task,),
                    daemon=True
                ).start()
    
    def _execute_task(self, task: Task):
        try:
            logger.info(
                "executing_task",
                extra={
                    "task_id": task.task_id,
                    "scheduled_for": task.execute_at.isoformat()
                }
            )
            
            task.execute()
            
            logger.info(
                "task_completed",
                extra={"task_id": task.task_id}
            )
        except Exception as e:
            logger.error(
                "task_execution_error",
                extra={
                    "task_id": task.task_id,
                    "error": str(e)
                }
            )


scheduler = TaskScheduler.get_instance()
