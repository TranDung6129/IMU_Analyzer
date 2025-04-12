# File: src/utils/threading_utils.py
# Purpose: Thread-safe utilities for working with queues and threads
# Target Lines: ≤150

"""
Methods to implement:
- safe_put(queue, item, timeout): Thread-safe queue put with timeout
- safe_get(queue, timeout): Thread-safe queue get with timeout
"""

import queue
import logging
import threading
from functools import wraps


def safe_put(queue_obj, item, timeout=1.0):
    """
    Thread-safe method to put an item into a queue with timeout.
    
    Args:
        queue_obj (queue.Queue): Queue to put item into
        item: Item to put in the queue
        timeout (float): Maximum time to wait in seconds
        
    Returns:
        bool: True if item was put in queue, False on timeout or queue full
        
    Raises:
        Exception: Any exception other than queue.Full
    """
    try:
        queue_obj.put(item, block=True, timeout=timeout)
        return True
    except queue.Full:
        return False
    except Exception as e:
        logging.error(f"Error in safe_put: {str(e)}")
        raise


def safe_get(queue_obj, timeout=1.0):
    """
    Thread-safe method to get an item from a queue with timeout.
    
    Args:
        queue_obj (queue.Queue): Queue to get item from
        timeout (float): Maximum time to wait in seconds
        
    Returns:
        tuple: (True, item) if successful, (False, None) on timeout or queue empty
        
    Raises:
        Exception: Any exception other than queue.Empty
    """
    try:
        item = queue_obj.get(block=True, timeout=timeout)
        return True, item
    except queue.Empty:
        return False, None
    except Exception as e:
        logging.error(f"Error in safe_get: {str(e)}")
        raise


# Additional utility functions (not implemented yet, just signatures)

# TODO: Implement thread shutdown function
# def shutdown_thread(thread, timeout=5.0):
#     pass

# TODO: Implement thread pool class
# class ThreadPool:
#     def __init__(self, max_workers=4):
#         pass
#     def submit(self, func, *args, **kwargs):
#         pass
#     def shutdown(self):
#         pass

# How to extend and modify:
# 1. Add thread pool: Implement a simple thread pool for task execution
# 2. Add lock utilities: Create helper functions for lock management
# 3. Add thread state monitoring: Add functionality to monitor thread health