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
import importlib
import inspect

from tornado.ioloop import IOLoop

from motioneye import settings

_INTERVAL = 2
_STATE_FILE_NAME = 'tasks.json'
_MAX_TASKS = 100
_POOL_SIZE = 1

_tasks = []
_pool = None
_safe_tasks_map = {}

# A safelist of modules that are allowed to provide task functions.
SAFE_TASK_MODULES = [
    'motioneye.cleanup',
    'motioneye.prefs',
    'motioneye.uploadservices',
]


def _populate_safe_tasks_map():
    """Dynamically populates the map of safe functions that can be called by tasks."""
    global _safe_tasks_map
    if _safe_tasks_map:
        return

    logging.debug("Populating safe tasks map...")
    for module_name in SAFE_TASK_MODULES:
        try:
            module = importlib.import_module(module_name)
            for name, func in inspect.getmembers(module, inspect.isfunction):
                full_name = f"{module_name}.{name}"
                _safe_tasks_map[full_name] = func
        except ImportError as e:
            logging.error(f"Failed to import safe task module {module_name}: {e}")
    logging.debug(f"Safe tasks map populated with {len(_safe_tasks_map)} functions.")


def start():
    global _pool

    _populate_safe_tasks_map()

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
    if isinstance(when, int):
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
        (when, func, tag, callback, params) = _tasks.pop(0)
        if func:
            logging.debug('executing task "%s"' % tag or func.__name__)
            _pool.apply_async(func, kwds=params, callback=callback if callable(callback) else None)
        changed = True

    if changed:
        _save()


def _load():
    global _tasks
    _tasks = []
    file_path = os.path.join(settings.CONF_PATH, _STATE_FILE_NAME)

    if not os.path.exists(file_path):
        legacy_pickle_path = os.path.join(settings.CONF_PATH, 'tasks.pickle')
        if os.path.exists(legacy_pickle_path):
            _convert_legacy_pickle_file(legacy_pickle_path)
        return

    logging.debug(f'loading tasks from "{file_path}"...')
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        if not isinstance(data, dict) or 'tasks' not in data:
            logging.warning("Invalid tasks file format, starting with empty task list")
            return

        for task_data in data['tasks']:
            if _validate_task_data(task_data):
                task = _reconstruct_task(task_data)
                if task:
                    _tasks.append(task)
            else:
                logging.warning(f"Invalid task data skipped: {task_data}")
        logging.debug(f'loaded {len(_tasks)} tasks from "{file_path}"')
    except Exception as e:
        logging.error(f'could not read tasks from file "{file_path}": {e}')


def _validate_task_data(task_data):
    if not isinstance(task_data, dict):
        return False
    return all(field in task_data for field in ['when', 'func_name', 'params'])


def _reconstruct_task(task_data):
    func_name = task_data.get('func_name')
    if not func_name or func_name not in _safe_tasks_map:
        logging.warning(f"Unsafe or unknown function in task data: {func_name}")
        return None

    func = _safe_tasks_map[func_name]
    return (task_data['when'], func, task_data.get('tag'), None, task_data.get('params', {}))


def _convert_legacy_pickle_file(pickle_file_path):
    try:
        import pickle
        backup_file = f"{pickle_file_path}.backup"
        os.rename(pickle_file_path, backup_file)

        with open(backup_file, 'rb') as f:
            legacy_tasks = pickle.load(f)

        global _tasks
        _tasks = []
        for task in legacy_tasks:
            if len(task) >= 5:
                when, func, tag, callback, params = task[:5]
                func_name = f"{getattr(func, '__module__', '')}.{getattr(func, '__name__', '')}"
                if func_name in _safe_tasks_map:
                    _tasks.append((when, _safe_tasks_map[func_name], tag, None, params))
                else:
                    logging.warning(f"Skipping unsafe function in legacy conversion: {func_name}")
        _save()
        logging.info("Successfully converted legacy pickle file to secure format")
        logging.info(f"Legacy file backed up as: {backup_file}")
    except Exception as e:
        logging.error(f"Error converting legacy pickle file: {e}")
        backup_file = f"{pickle_file_path}.backup"
        if os.path.exists(backup_file):
            os.rename(backup_file, pickle_file_path)


def _save():
    file_path = os.path.join(settings.CONF_PATH, _STATE_FILE_NAME)
    logging.debug('saving tasks to "%s"...' % file_path)
    serializable_tasks = []
    for task in _tasks:
        if len(task) >= 5:
            when, func, tag, callback, params = task[:5]
            if callback:
                continue

            func_name = f"{getattr(func, '__module__', '')}.{getattr(func, '__name__', '')}"
            if func and func_name in _safe_tasks_map:
                serializable_tasks.append({
                    'when': when,
                    'func_name': func_name,
                    'tag': tag,
                    'params': params,
                })

    data = {'tasks': serializable_tasks, 'version': '2.2', 'format': 'secure_json'}
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logging.debug(f'saved {len(serializable_tasks)} tasks to "{file_path}"')
    except Exception as e:
        logging.error(f'could not save tasks to file "{file_path}": {e}')