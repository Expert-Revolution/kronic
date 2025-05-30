import logging

from kubernetes import client
from kubernetes import config as kubeconfig
from kubernetes.config import ConfigException
from kubernetes.client.rest import ApiException
from datetime import datetime, timezone
from typing import List

import config

log = logging.getLogger("app.kron")

if not config.TEST:
    try:
        # Load configuration inside the Pod
        kubeconfig.load_incluster_config()
    except ConfigException:
        # Load configuration from KUBECONFIG
        kubeconfig.load_kube_config()

# Create the Api clients
v1 = client.CoreV1Api()
batch = client.BatchV1Api()
generic = client.ApiClient()


def namespace_filter(func):
    """Decorator that short-circuits and returns False if the wrapped function attempts to access an unlisted namespace

    Args:
        func (function): The function to wrap. Must have `namespace` as an arg to itself
    """

    def wrapper(namespace: str = None, *args, **kwargs):
        if config.ALLOW_NAMESPACES and namespace:
            if namespace in config.ALLOW_NAMESPACES.split(","):
                log.debug(
                    f"Namespace access granted for '{namespace}' (in allowed list)"
                )
                return func(namespace, *args, **kwargs)
            else:
                log.warning(
                    f"Namespace access denied for '{namespace}' (not in allowed list: {config.ALLOW_NAMESPACES})"
                )
        else:
            if namespace:
                log.debug(
                    f"Namespace access granted for '{namespace}' (no restrictions configured)"
                )
            else:
                log.debug(
                    "Namespace access granted for all namespaces (no restrictions configured)"
                )
            return func(namespace, *args, **kwargs)

        return False

    return wrapper


def _filter_dict_fields(items: List[dict], fields: List[str] = ["name"]) -> List[dict]:
    """
    Filter a given list of API object down to only the metadata fields listed.

    Args:
        response (Obj): A kubernetes client API object or object list.
        filds (List of str): The desired fields to retain from the object

    Returns:
        dict: The object is converted to a dict and retains only the fields
            provided.

    """
    return [
        {field: item.get("metadata").get(field) for field in fields} for item in items
    ]


def _clean_api_object(api_object: object) -> dict:
    """Convert API object to JSON and strip managedFields"""
    api_dict = generic.sanitize_for_serialization(api_object)
    api_dict["metadata"].pop("managedFields", None)
    return api_dict


def _get_time_since(datestring: str) -> str:
    """
    Calculate the time difference between the input datestring and the current time
    and return a human-readable string.

    Args:
        datestring (str): A string representing a timestamp in ISO format.

    Returns:
        str: A human-readable time difference string.
    """
    current_time = datetime.now(timezone.utc)
    input_time = datetime.fromisoformat(datestring)

    time_difference = current_time - input_time

    if time_difference.total_seconds() < 0:
        return "In the future"

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"


def _has_label(api_object: object, k: str, v: str) -> bool:
    """
    Return True if a label is present with the specified key and value.

    Args:
        api_object (dict): The API object with metadata.
        k (str): The label key to check.
        v (str): The label value to check.

    Returns:
        bool: True if the label is present with the specified key and value, otherwise False.
    """
    metadata = api_object.get("metadata", {})
    labels = metadata.get("labels", {})
    return labels.get(k) == v


def _interpret_cron_schedule(cron_expression: str) -> str:
    """
    Convert a cron expression to human-readable text.

    Args:
        cron_expression (str): A cron expression (e.g., "*/10 * * * *")

    Returns:
        str: Human-readable description of the schedule
    """
    if not cron_expression or not isinstance(cron_expression, str):
        return "Invalid schedule"

    parts = cron_expression.strip().split()
    if len(parts) != 5:
        return "Invalid cron format"

    minute, hour, day, month, weekday = parts

    # Handle common patterns
    if cron_expression == "* * * * *":
        return "Every minute"

    if (
        minute.startswith("*/")
        and hour == "*"
        and day == "*"
        and month == "*"
        and weekday == "*"
    ):
        interval = minute[2:]
        if interval == "1":
            return "Every minute"
        else:
            return f"Every {interval} minutes"

    if (
        minute == "0"
        and hour.startswith("*/")
        and day == "*"
        and month == "*"
        and weekday == "*"
    ):
        interval = hour[2:]
        if interval == "1":
            return "Every hour"
        else:
            return f"Every {interval} hours"

    if minute == "0" and hour == "0" and day == "*" and month == "*" and weekday == "*":
        return "Daily at midnight"

    if minute == "0" and hour == "0" and day == "*" and month == "*" and weekday == "0":
        return "Weekly on Sunday at midnight"

    if minute == "0" and hour == "0" and day == "1" and month == "*" and weekday == "*":
        return "Monthly on the 1st at midnight"

    # Handle specific times
    if (
        hour.isdigit()
        and minute.isdigit()
        and day == "*"
        and month == "*"
        and weekday == "*"
    ):
        hour_int = int(hour)
        minute_int = int(minute)
        time_str = f"{hour_int:02d}:{minute_int:02d}"
        return f"Daily at {time_str}"

    # Handle specific weekdays
    if (
        minute.isdigit()
        and hour.isdigit()
        and day == "*"
        and month == "*"
        and weekday.isdigit()
    ):
        hour_int = int(hour)
        minute_int = int(minute)
        weekday_int = int(weekday)
        weekdays = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
        ]
        if 0 <= weekday_int <= 6:
            time_str = f"{hour_int:02d}:{minute_int:02d}"
            return f"Weekly on {weekdays[weekday_int]} at {time_str}"

    # Handle monthly schedules
    if (
        minute.isdigit()
        and hour.isdigit()
        and day.isdigit()
        and month == "*"
        and weekday == "*"
    ):
        hour_int = int(hour)
        minute_int = int(minute)
        day_int = int(day)
        time_str = f"{hour_int:02d}:{minute_int:02d}"
        return f"Monthly on the {day_int} at {time_str}"

    # Fallback for complex expressions
    return f"Custom schedule: {cron_expression}"


def pod_is_owned_by(api_dict: dict, owner_name: str) -> bool:
    """Return whether a job or pod contains an ownerReference to the given cronjob or job name

    Args:
        object (dict): A dict representation of a job or pod
        owner_name (str): The name of a cronjob or job which may have created the given job or pod

    Returns:
        bool: True if an ownerReference contains the given owner_name
    """
    owner_references = api_dict["metadata"].get("ownerReferences", [])
    return any(owner_ref["name"] == owner_name for owner_ref in owner_references)


@namespace_filter
def get_cronjobs(namespace: str = None) -> List[dict]:
    """Get names of cronjobs in a given namespace. If namespace is not provided, return CronJobs
        from all namespaces.

    Args:
        namespace (str, optional): namespace to examine. Defaults to "" (all namespaces).

    Returns:
        List of dict: A list of dicts containing the name and namespace of each cronjob.
    """
    try:
        cronjobs = []
        if not namespace:
            if not config.ALLOW_NAMESPACES:
                log.debug("Listing cronjobs for all namespaces")
                cronjobs = [
                    _clean_api_object(item)
                    for item in batch.list_cron_job_for_all_namespaces().items
                ]
            else:
                log.debug(
                    f"Listing cronjobs for allowed namespaces: {config.ALLOW_NAMESPACES}"
                )
                cronjobs = []
                for allowed in config.ALLOW_NAMESPACES.split(","):
                    cronjobs.extend(
                        [
                            _clean_api_object(item)
                            for item in batch.list_namespaced_cron_job(
                                namespace=allowed
                            ).items
                        ]
                    )
        else:
            log.debug(f"Listing cronjobs for namespace '{namespace}'")
            cronjobs = [
                _clean_api_object(item)
                for item in batch.list_namespaced_cron_job(namespace=namespace).items
            ]

        fields = ["name", "namespace"]
        sorted_cronjobs = sorted(
            _filter_dict_fields(cronjobs, fields), key=lambda x: x["name"]
        )
        log.info(
            f"Retrieved {len(sorted_cronjobs)} cronjobs"
            + (f" from namespace '{namespace}'" if namespace else "")
        )
        return sorted_cronjobs

    except ApiException as e:
        log.error(
            f"Kubernetes API error while getting cronjobs: {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def get_cronjob(namespace: str, cronjob_name: str) -> dict:
    """Get the details of a given CronJob as a dict

    Args:
        namespace (str): The namespace
        cronjob_name (str): The name of an existing CronJob

    Returns:
        dict: A dict of the CronJob API object
    """
    try:
        log.debug(f"Getting cronjob '{cronjob_name}' in namespace '{namespace}'")
        cronjob = batch.read_namespaced_cron_job(cronjob_name, namespace)
        log.debug(
            f"Successfully retrieved cronjob '{cronjob_name}' from namespace '{namespace}'"
        )
        return _clean_api_object(cronjob)
    except ApiException as e:
        if e.status == 404:
            log.warning(
                f"CronJob '{cronjob_name}' not found in namespace '{namespace}'"
            )
        else:
            log.error(
                f"Kubernetes API error while getting cronjob '{cronjob_name}': {e.reason} (status: {e.status})"
            )
        return False


@namespace_filter
def get_jobs(namespace: str, cronjob_name: str) -> List[dict]:
    """Return jobs belonging to a given CronJob name

    Args:
        namespace (str): The namespace
        cronjob_name (str): The CronJob which owns jobs to return

    Returns:
        List of dicts: A list of dicts of each job created by the given CronJob name
    """
    try:
        log.debug(
            f"Getting jobs for cronjob '{cronjob_name}' in namespace '{namespace}'"
        )
        jobs = batch.list_namespaced_job(namespace=namespace)
        cleaned_jobs = [_clean_api_object(job) for job in jobs.items]

        filtered_jobs = [
            job
            for job in cleaned_jobs
            if pod_is_owned_by(job, cronjob_name)
            or _has_label(job, "kronic.mshade.org/created-from", cronjob_name)
        ]

        for job in filtered_jobs:
            job["status"]["age"] = _get_time_since(job["status"]["startTime"])

        log.info(
            f"Retrieved {len(filtered_jobs)} jobs for cronjob '{cronjob_name}' in namespace '{namespace}'"
        )
        return filtered_jobs

    except ApiException as e:
        log.error(
            f"Kubernetes API error while getting jobs for cronjob '{cronjob_name}': {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def get_pods(namespace: str, job_name: str = None) -> List[dict]:
    """Return pods related to jobs in a namespace

    Args:
        namespace (str): The namespace from which to fetch pods
        job_name (str, optional): Fetch pods owned by jobs. Defaults to None.

    Returns:
        List of dicts: A list of pod dicts
    """
    try:
        all_pods = v1.list_namespaced_pod(namespace=namespace)
        cleaned_pods = [_clean_api_object(pod) for pod in all_pods.items]
        filtered_pods = [
            pod
            for pod in cleaned_pods
            if pod_is_owned_by(pod, job_name) or (not job_name)
        ]

        for pod in filtered_pods:
            pod["status"]["age"] = _get_time_since(pod["status"]["startTime"])

        return filtered_pods

    except ApiException as e:
        log.error(e)
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def get_jobs_and_pods(namespace: str, cronjob_name: str) -> List[dict]:
    """Get jobs and their pods under a `pods` element for display purposes

    Args:
        namespace (str): The namespace
        cronjob_name (str): The CronJob name to filter jobs and pods by

    Returns:
        List of dicts: A list of job dicts, each with a jobs element containing a list of pods the job created
    """
    jobs = get_jobs(namespace, cronjob_name)
    all_pods = get_pods(namespace)
    for job in jobs:
        job["pods"] = [
            pod for pod in all_pods if pod_is_owned_by(pod, job["metadata"]["name"])
        ]

    return jobs


@namespace_filter
def get_pod_logs(namespace: str, pod_name: str) -> str:
    """Return plain text logs for <pod_name> in <namespace>"""
    try:
        log.debug(f"Getting logs for pod '{pod_name}' in namespace '{namespace}'")
        logs = v1.read_namespaced_pod_log(
            pod_name, namespace, tail_lines=1000, timestamps=True
        )
        log.debug(
            f"Successfully retrieved logs for pod '{pod_name}' in namespace '{namespace}'"
        )
        return logs

    except ApiException as e:
        if e.status == 404:
            error_msg = f"Kronic> Error fetching logs: {e.reason}"
            log.warning(
                f"Pod '{pod_name}' not found in namespace '{namespace}' when getting logs"
            )
            return error_msg
        else:
            error_msg = f"Kronic> Error fetching logs: {e.reason}"
            log.error(
                f"Kubernetes API error while getting logs for pod '{pod_name}': {e.reason} (status: {e.status})"
            )
            return error_msg


@namespace_filter
def trigger_cronjob(namespace: str, cronjob_name: str) -> dict:
    try:
        log.info(f"Triggering cronjob '{cronjob_name}' in namespace '{namespace}'")
        # Retrieve the CronJob template
        cronjob = batch.read_namespaced_cron_job(name=cronjob_name, namespace=namespace)
        job_template = cronjob.spec.job_template

        # Create a unique name indicating a manual invocation
        date_stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S-%f")
        job_template.metadata.name = (
            f"{cronjob.metadata.name[:16]}-manual-{date_stamp}"[:63]
        )

        # Set labels to identify jobs created by kronic
        job_template.metadata.labels = {
            "kronic.mshade.org/manually-triggered": "true",
            "kronic.mshade.org/created-from": cronjob_name,
        }

        log.debug(
            f"Creating manual job '{job_template.metadata.name}' from cronjob '{cronjob_name}'"
        )
        trigger_job = batch.create_namespaced_job(
            body=job_template, namespace=namespace
        )
        log.info(
            f"Successfully triggered cronjob '{cronjob_name}' in namespace '{namespace}' - created job '{job_template.metadata.name}'"
        )
        return _clean_api_object(trigger_job)

    except ApiException as e:
        log.error(
            f"Kubernetes API error while triggering cronjob '{cronjob_name}': {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def toggle_cronjob_suspend(namespace: str, cronjob_name: str) -> dict:
    """Toggle a CronJob's suspend flag on or off

    Args:
        namespace (str): The namespace
        cronjob_name (str): The cronjob name

    Returns:
        dict: The full cronjob object is returned as a dict
    """
    try:
        log.debug(
            f"Getting current suspend status for cronjob '{cronjob_name}' in namespace '{namespace}'"
        )
        suspended_status = batch.read_namespaced_cron_job_status(
            name=cronjob_name, namespace=namespace
        )
        current_suspend = suspended_status.spec.suspend
        new_suspend = not current_suspend

        log.info(
            f"Toggling cronjob '{cronjob_name}' suspend status from {current_suspend} to {new_suspend} in namespace '{namespace}'"
        )
        patch_body = {"spec": {"suspend": new_suspend}}
        cronjob = batch.patch_namespaced_cron_job(
            name=cronjob_name, namespace=namespace, body=patch_body
        )
        log.info(
            f"Successfully {'suspended' if new_suspend else 'resumed'} cronjob '{cronjob_name}' in namespace '{namespace}'"
        )
        return _clean_api_object(cronjob)

    except ApiException as e:
        log.error(
            f"Kubernetes API error while toggling suspend for cronjob '{cronjob_name}': {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def update_cronjob(namespace: str, spec: str) -> dict:
    """Update/edit a CronJob configuration via patch

    Args:
        namespace (str): The namespace
        spec (dict): A cronjob spec as a dict object

    Returns:
        dict: Returns the updated cronjob spec as a dict, or an error response
    """
    try:
        name = spec["metadata"]["name"]
        if get_cronjob(namespace, name):
            log.info(f"Updating existing cronjob '{name}' in namespace '{namespace}'")
            cronjob = batch.patch_namespaced_cron_job(name, namespace, spec)
        else:
            log.info(f"Creating new cronjob '{name}' in namespace '{namespace}'")
            cronjob = batch.create_namespaced_cron_job(namespace, spec)

        log.info(
            f"Successfully updated/created cronjob '{name}' in namespace '{namespace}'"
        )
        return _clean_api_object(cronjob)

    except ApiException as e:
        log.error(
            f"Kubernetes API error while updating cronjob '{spec.get('metadata', {}).get('name', 'unknown')}': {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def delete_cronjob(namespace: str, cronjob_name: str) -> dict:
    """Delete a CronJob

    Args:
        namespace (str): The namespace
        cronjob_name (str): The name of the CronJob to delete

    Returns:
        dict: Returns a dict of the deleted CronJob, or an error status
    """
    try:
        log.info(f"Deleting cronjob '{cronjob_name}' in namespace '{namespace}'")
        deleted = batch.delete_namespaced_cron_job(cronjob_name, namespace)
        log.info(
            f"Successfully deleted cronjob '{cronjob_name}' from namespace '{namespace}'"
        )
        return _clean_api_object(deleted)

    except ApiException as e:
        log.error(
            f"Kubernetes API error while deleting cronjob '{cronjob_name}': {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response


@namespace_filter
def delete_job(namespace: str, job_name: str) -> dict:
    """Delete a Job

    Args:
        namespace (str): The namespace
        job_name (str): The name of the Job to delete

    Returns:
        str: Returns a dict of the deleted Job, or an error status
    """
    try:
        log.info(f"Deleting job '{job_name}' in namespace '{namespace}'")
        deleted = batch.delete_namespaced_job(job_name, namespace)
        log.info(f"Successfully deleted job '{job_name}' from namespace '{namespace}'")
        return _clean_api_object(deleted)

    except ApiException as e:
        log.error(
            f"Kubernetes API error while deleting job '{job_name}': {e.reason} (status: {e.status})"
        )
        response = {
            "error": 500,
            "exception": {
                "status": e.status,
                "reason": e.reason,
                "message": e.body["message"],
            },
        }
        return response
