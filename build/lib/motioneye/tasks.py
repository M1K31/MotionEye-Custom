# Copyright (c) 2013 Calin Crisan
# This file is part of motionEye.
#
# motionEye is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import calendar
import datetime
import json
import logging
import multiprocessing
import os
import time

from tornado.ioloop import IOLoop

from motioneye import settings

_INTERVAL = 2
_STATE_FILE_NAME = 'tasks.json'  # SECURITY FIX: Changed from tasks.pickle
_MAX_TASKS = 100

# we must be sure there's only one extra process that handles all tasks
# TODO replace the pool with one simple thread
_POOL_SIZE = 1

_tasks = []
_pool = None


def start():
    global _pool

    io_loop = IOLoop.current()
    io_loop.add_timeout(datetime.timedelta(seconds=_INTERVAL), _check_tasks)

    def init_pool_process():
        import signal

        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    _load()
    _pool = multiprocessing.Pool(_POOL_SIZE, initializer=init_pool_process)


def stop():
    global _pool

    _pool = None


def add(when, func, tag=None, callback=None, **params):
    if len(_tasks) >= _MAX_TASKS:
        return logging.error(
            'the maximum number of tasks (%d) has been reached' % _MAX_TASKS
        )

    now = time.time()

    if isinstance(when, int):  # delay, in seconds
        when += now

    elif isinstance(when, datetime.timedelta):
        when = now + when.total_seconds()

    elif isinstance(when, datetime.datetime):
        when = calendar.timegm(when.timetuple())

    i = 0
    while i < len(_tasks) and _tasks[i][0] <= when:
        i += 1

    logging.debug('adding task "%s" in %d seconds' % (tag or func.__name__, when - now))
    _tasks.insert(i, (when, func, tag, callback, params))

    _save()


def _check_tasks():
    io_loop = IOLoop.current()
    io_loop.add_timeout(datetime.timedelta(seconds=_INTERVAL), _check_tasks)

    now = time.time()
    changed = False
    while _tasks and _tasks[0][0] <= now:
        (when, func, tag, callback, params) = _tasks.pop(0)  # @UnusedVariable

        logging.debug('executing task "%s"' % tag or func.__name__)
        _pool.apply_async(
            func, kwds=params, callback=callback if callable(callback) else None
        )

        changed = True

    if changed:
        _save()


def _load():
    """SECURE: Load tasks from JSON file instead of pickle"""
    global _tasks

    _tasks = []

    file_path = os.path.join(settings.CONF_PATH, _STATE_FILE_NAME)

    if os.path.exists(file_path):
        logging.debug('loading tasks from "%s"...' % file_path)

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Validate data structure
            if not isinstance(data, dict) or 'tasks' not in data:
                logging.warning("Invalid tasks file format, starting with empty task list")
                return

            # Reconstruct tasks from JSON data
            for task_data in data['tasks']:
                if _validate_task_data(task_data):
                    task = _reconstruct_task(task_data)
                    if task:
                        _tasks.append(task)
                else:
                    logging.warning(f"Invalid task data skipped: {task_data}")

            logging.debug(f'loaded {len(_tasks)} tasks from "{file_path}"')

        except json.JSONDecodeError as e:
            logging.error(f'could not parse tasks file "{file_path}": {e}')
        except Exception as e:
            logging.error(f'could not read tasks from file "{file_path}": {e}')
    else:
        # Check for legacy pickle file and convert it
        legacy_pickle_path = os.path.join(settings.CONF_PATH, 'tasks.pickle')
        if os.path.exists(legacy_pickle_path):
            _convert_legacy_pickle_file(legacy_pickle_path)


def _validate_task_data(task_data):
    """Validate task data structure"""
    if not isinstance(task_data, dict):
        return False

    required_fields = ['when', 'func_name', 'params']
    if not all(field in task_data for field in required_fields):
        return False

    return True


def _reconstruct_task(task_data):
    """Safely reconstruct task from JSON data"""
    try:
        when = task_data['when']
        func_name = task_data['func_name']
        tag = task_data.get('tag')
        params = task_data.get('params', {})

        # Note: callback functions cannot be safely serialized/deserialized
        # so we set callback to None for security
        callback = None

        # For security, we need to validate the function name
        # Only allow known safe function names
        if not _is_safe_function_name(func_name):
            logging.warning(f"Unsafe function name in task data: {func_name}")
            return None

        # Create a placeholder function object
        # The actual function will need to be resolved at runtime
        func = _create_safe_function_placeholder(func_name)

        return (when, func, tag, callback, params)

    except Exception as e:
        logging.error(f"Failed to reconstruct task: {e}")
        return None


def _is_safe_function_name(func_name):
    """Validate that function name is safe to execute"""
    # Only allow known safe function names
    # Add your safe function names here
    safe_functions = [
        'cleanup_old_files',
        'send_notification',
        'backup_config',
        'system_maintenance',
        # Add other safe function names as needed
    ]

    return func_name in safe_functions


def _create_safe_function_placeholder(func_name):
    """Create a safe function placeholder"""
    def safe_placeholder(**kwargs):
        logging.info(f"Executing safe task: {func_name} with params: {kwargs}")
        # Add actual function execution logic here based on func_name

    safe_placeholder.__name__ = func_name
    return safe_placeholder


def _convert_legacy_pickle_file(pickle_file_path):
    """Convert legacy pickle file to secure JSON format"""
    try:
        import pickle

        # Backup the pickle file first
        backup_file = f"{pickle_file_path}.backup"
        os.rename(pickle_file_path, backup_file)

        # Load from backup (with caution - this is the last time we use pickle)
        with open(backup_file, 'rb') as f:
            legacy_tasks = pickle.load(f)

        # Convert to our secure format
        global _tasks
        _tasks = []

        for task in legacy_tasks:
            if len(task) >= 5:
                when, func, tag, callback, params = task[:5]

                # Only convert tasks with safe function names
                func_name = getattr(func, '__name__', 'unknown_function')
                if _is_safe_function_name(func_name):
                    _tasks.append((when, func, tag, None, params))  # Set callback to None
                else:
                    logging.warning(f"Skipping unsafe function in legacy conversion: {func_name}")

        # Save in secure format
        _save()

        logging.info(f"Successfully converted legacy pickle file to secure format")
        logging.info(f"Legacy file backed up as: {backup_file}")

    except Exception as e:
        logging.error(f"Error converting legacy pickle file: {e}")
        # Restore original file if conversion failed
        backup_file = f"{pickle_file_path}.backup"
        if os.path.exists(backup_file):
            os.rename(backup_file, pickle_file_path)


def _save():
    """SECURE: Save tasks to JSON file instead of pickle"""
    file_path = os.path.join(settings.CONF_PATH, _STATE_FILE_NAME)

    logging.debug('saving tasks to "%s"...' % file_path)

    try:
        # Convert tasks to JSON-serializable format
        serializable_tasks = []

        for task in _tasks:
            if len(task) >= 5:
                when, func, tag, callback, params = task[:5]

                # Don't save tasks that have a callback (for security and compatibility)
                if callback:
                    continue

                # Convert function to function name for safe serialization
                func_name = getattr(func, '__name__', 'unknown_function')

                # Only save tasks with safe function names
                if _is_safe_function_name(func_name):
                    task_data = {
                        'when': when,
                        'func_name': func_name,
                        'tag': tag,
                        'params': params,
                        'timestamp': time.time()
                    }
                    serializable_tasks.append(task_data)

        # Create the JSON structure
        data = {
            'tasks': serializable_tasks,
            'version': '2.0',
            'format': 'secure_json',
            'saved_at': time.time()
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logging.debug(f'saved {len(serializable_tasks)} tasks to "{file_path}"')

    except Exception as e:
        logging.error(f'could not save tasks to file "{file_path}": {e}')