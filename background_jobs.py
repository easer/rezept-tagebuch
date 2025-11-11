"""
Background Job Manager for Long-Running Import Tasks

Provides async job execution for:
- TheMealDB imports (with DeepL translation)
- Migusto batch imports

Jobs run in background threads and can be monitored via job_id.
"""

import threading
import uuid
import time
from datetime import datetime
from typing import Dict, Any, Callable

# Global job storage (in-memory)
# In production, this could be Redis or database-backed
_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()

# Job status constants
STATUS_PENDING = 'pending'
STATUS_RUNNING = 'running'
STATUS_COMPLETED = 'completed'
STATUS_FAILED = 'failed'


def create_job(job_type: str, params: Dict[str, Any]) -> str:
    """
    Create a new background job

    Args:
        job_type: Type of job (e.g., 'themealdb_import', 'migusto_import')
        params: Job parameters

    Returns:
        job_id: Unique job identifier
    """
    job_id = str(uuid.uuid4())

    with _jobs_lock:
        _jobs[job_id] = {
            'job_id': job_id,
            'job_type': job_type,
            'status': STATUS_PENDING,
            'params': params,
            'result': None,
            'error': None,
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'progress': {
                'current': 0,
                'total': 0,
                'message': 'Job created'
            }
        }

    return job_id


def get_job(job_id: str) -> Dict[str, Any]:
    """
    Get job status and result

    Args:
        job_id: Job identifier

    Returns:
        Job details or None if not found
    """
    with _jobs_lock:
        return _jobs.get(job_id)


def update_job_progress(job_id: str, current: int, total: int, message: str):
    """Update job progress"""
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]['progress'] = {
                'current': current,
                'total': total,
                'message': message
            }


def run_job_in_background(job_id: str, worker_func: Callable, app_context):
    """
    Execute job in background thread

    Args:
        job_id: Job identifier
        worker_func: Function to execute (must accept job_id, params, app_context)
        app_context: Flask app context
    """
    def _worker():
        with _jobs_lock:
            if job_id not in _jobs:
                return
            _jobs[job_id]['status'] = STATUS_RUNNING
            _jobs[job_id]['started_at'] = datetime.utcnow().isoformat()
            params = _jobs[job_id]['params']

        try:
            # Execute worker function
            result = worker_func(job_id, params, app_context)

            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]['status'] = STATUS_COMPLETED
                    _jobs[job_id]['result'] = result
                    _jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()

        except Exception as e:
            with _jobs_lock:
                if job_id in _jobs:
                    _jobs[job_id]['status'] = STATUS_FAILED
                    _jobs[job_id]['error'] = str(e)
                    _jobs[job_id]['completed_at'] = datetime.utcnow().isoformat()

    # Start background thread
    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()


def cleanup_old_jobs(max_age_hours: int = 24):
    """
    Remove completed jobs older than max_age_hours

    Args:
        max_age_hours: Maximum age in hours
    """
    cutoff = datetime.utcnow().timestamp() - (max_age_hours * 3600)

    with _jobs_lock:
        to_remove = []
        for job_id, job in _jobs.items():
            if job['completed_at']:
                completed_at = datetime.fromisoformat(job['completed_at']).timestamp()
                if completed_at < cutoff:
                    to_remove.append(job_id)

        for job_id in to_remove:
            del _jobs[job_id]

    return len(to_remove)


def get_all_jobs(limit: int = 50) -> list:
    """
    Get all jobs (for debugging/monitoring)

    Args:
        limit: Maximum number of jobs to return

    Returns:
        List of jobs, newest first
    """
    with _jobs_lock:
        jobs = sorted(
            _jobs.values(),
            key=lambda x: x['created_at'],
            reverse=True
        )
        return jobs[:limit]
