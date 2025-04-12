# File: src/utils/sync_utils.py
# Purpose: Synchronization and threading utilities
# Target Lines: ≤150

"""
Methods to implement:
- run_in_thread(func): Run a function in a separate thread
- async_wrapper(func, *args, **kwargs): Run a function asynchronously
"""

import threading
import logging
import asyncio
import functools
import concurrent.futures


def run_in_thread(func):
    """
    Decorator to run a function in a separate thread.
    
    Args:
        func (callable): The function to run in a thread
        
    Returns:
        callable: Wrapped function that runs in a thread
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
        
    return wrapper


def async_wrapper(func, *args, **kwargs):
    """
    Run a function asynchronously and return a future.
    
    Args:
        func (callable): The function to run asynchronously
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        concurrent.futures.Future: Future object that will contain the result
    """
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(func, *args, **kwargs)
    
    # Add a callback to shutdown the executor when done
    def done_callback(f):
        executor.shutdown(wait=False)
    
    future.add_done_callback(done_callback)
    return future


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement rate limiter decorator
# def rate_limit(calls_per_second):
#     pass

# TODO: Implement periodic task runner
# def periodic_task(interval_seconds):
#     pass

# TODO: Implement task queue processor
# class TaskQueue:
#     pass

# How to extend and modify:
# 1. Add async/await support: Add utilities for asyncio integration
# 2. Add thread pool: Create a reusable thread pool implementation
# 3. Add task prioritization: Add functionality for task priority handling