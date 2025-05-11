"""
Task scheduler for handling background jobs in Coin Clash.
This module manages scheduled tasks like match auto-start at timer expiry.
"""

import logging
import threading
import time
import datetime
import heapq
from typing import Callable, Dict, List, Any, Optional, Tuple
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
        """
        Initialize a new task.
        
        Args:
            task_id: Unique identifier for the task
            execute_at: When to execute the task
            callback: Function to call when task executes
            args: Positional arguments for the callback
            kwargs: Keyword arguments for the callback
        """
        self.task_id = task_id
        self.execute_at = execute_at
        self.callback = callback
        self.args = args or ()
        self.kwargs = kwargs or {}
        
    def __lt__(self, other):
        """Compare tasks by execution time for the priority queue."""
        return self.execute_at < other.execute_at
        
    def execute(self):
        """Execute the task's callback function."""
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
        """Initialize the task scheduler."""
        self.tasks = []  # Priority queue of tasks
        self.tasks_by_id = {}  # Map of task_id to Task objects
        self.lock = threading.RLock()  # Lock for thread safety
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
        
        Args:
            task_id: Unique identifier for the task
            execute_at: When to execute the task
            callback: Function to call when task executes
            *args: Positional arguments for the callback
            **kwargs: Keyword arguments for the callback
            
        Returns:
            The scheduled Task object
            
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
        """
        Schedule a match to start at the specified time.
        
        Args:
            match_id: ID of the match to start
            execute_at: When to start the match
            match_service_factory: Function that creates a MatchService
            
        Returns:
            The scheduled Task object
        """
        task_id = f"match_start_{match_id}_{execute_at.timestamp()}"
        
        def start_match_task():
            try:
                # Create a fresh service with a new DB session
                match_service = match_service_factory()
                # Only start if still in pending state
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
        """
        Cancel a scheduled task by ID.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was found and canceled, False otherwise
        """
        with self.lock:
            if task_id in self.tasks_by_id:
                # Mark the task as canceled by removing from the tasks_by_id dict
                # The task will still be in the heap but will be skipped when processed
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
        """Start the scheduler thread."""
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
        """Stop the scheduler thread."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
            self.scheduler_thread = None
            
        logger.info("scheduler_stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop that processes tasks."""
        while self.running:
            try:
                self._process_due_tasks()
                # Sleep for a short time to avoid busy-waiting
                time.sleep(1.0)
            except Exception as e:
                logger.error(
                    "scheduler_loop_error",
                    extra={"error": str(e)}
                )
    
    def _process_due_tasks(self):
        """Process all tasks that are due to be executed."""
        now = datetime.datetime.now(datetime.timezone.utc)
        
        with self.lock:
            # Process tasks that are due
            while self.tasks and self.tasks[0].execute_at <= now:
                task = heapq.heappop(self.tasks)
                
                # Skip if task was canceled
                if task.task_id not in self.tasks_by_id:
                    continue
                    
                # Remove from tasks_by_id before execution
                del self.tasks_by_id[task.task_id]
                
                # Execute the task outside the lock
                threading.Thread(
                    target=self._execute_task,
                    args=(task,),
                    daemon=True
                ).start()
    
    def _execute_task(self, task: Task):
        """Execute a task in a separate thread."""
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


# Singleton instance
scheduler = TaskScheduler.get_instance()
