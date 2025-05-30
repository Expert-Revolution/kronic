from flask import Flask, request, render_template, redirect
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

from functools import wraps
import yaml
from yaml.scanner import ScannerError
from yaml.parser import ParserError

import config
from kron import (
    get_cronjobs,
    get_jobs,
    get_jobs_and_pods,
    get_cronjob,
    get_pods,
    get_pod_logs,
    pod_is_owned_by,
    toggle_cronjob_suspend,
    trigger_cronjob,
    update_cronjob,
    delete_cronjob,
    delete_job,
    _interpret_cron_schedule,
)

app = Flask(__name__, static_url_path="", static_folder="static")
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username, password):
    # No users defined, so no auth enabled
    if not config.USERS:
        return True
    else:
        if username in config.USERS and check_password_hash(
            config.USERS.get(username), password
        ):
            return username


# A namespace filter decorator
def namespace_filter(func):
    @wraps(func)
    def wrapper(namespace, *args, **kwargs):
        if config.ALLOW_NAMESPACES:
            if namespace in config.ALLOW_NAMESPACES.split(","):
                return func(namespace, *args, **kwargs)
        else:
            return func(namespace, *args, **kwargs)

        data = {
            "error": f"Request to {namespace} denied due to KRONIC_ALLOW_NAMESPACES setting",
            "namespace": namespace,
        }
        if request.headers.get(
            "content-type", None
        ) == "application/json" or request.base_url.startswith("/api/"):
            return data, 403
        else:
            return render_template("denied.html", data=data)

    return wrapper


def _validate_cronjob_yaml(yaml_content):
    """Validate YAML syntax and CronJob structure

    Args:
        yaml_content (str): The YAML content to validate

    Returns:
        tuple: (is_valid, parsed_content, error_message)
    """
    try:
        # First validate YAML syntax
        parsed = yaml.safe_load(yaml_content)
    except (ScannerError, ParserError) as e:
        return False, None, f"Invalid YAML syntax: {str(e)}"
    except Exception as e:
        return False, None, f"Error parsing YAML: {str(e)}"

    # Check if it's a dictionary
    if not isinstance(parsed, dict):
        return False, None, "YAML must be a dictionary/object"

    # Validate basic CronJob structure
    required_fields = ["apiVersion", "kind", "metadata", "spec"]
    for field in required_fields:
        if field not in parsed:
            return False, None, f"Missing required field: {field}"

    # Validate kind is CronJob
    if parsed.get("kind") != "CronJob":
        return False, None, f"Expected kind 'CronJob', got '{parsed.get('kind')}'"

    # Validate apiVersion
    valid_api_versions = ["batch/v1", "batch/v1beta1"]
    if parsed.get("apiVersion") not in valid_api_versions:
        return (
            False,
            None,
            f"Invalid apiVersion '{parsed.get('apiVersion')}'. Expected one of: {', '.join(valid_api_versions)}",
        )

    # Validate metadata has name
    metadata = parsed.get("metadata", {})
    if not isinstance(metadata, dict):
        return False, None, "metadata must be a dictionary"

    if not metadata.get("name"):
        return False, None, "metadata.name is required"

    # Validate spec has required fields
    spec = parsed.get("spec", {})
    if not isinstance(spec, dict):
        return False, None, "spec must be a dictionary"

    schedule = spec.get("schedule")
    if not schedule:
        return False, None, "spec.schedule is required"

    # Basic cron schedule validation (should have 5 fields)
    if isinstance(schedule, str):
        schedule_parts = schedule.strip().split()
        if len(schedule_parts) != 5:
            return (
                False,
                None,
                f"spec.schedule '{schedule}' is invalid. Cron schedule must have exactly 5 fields (minute hour day-of-month month day-of-week)",
            )

    if not spec.get("jobTemplate"):
        return False, None, "spec.jobTemplate is required"

    job_template = spec.get("jobTemplate", {})
    if not isinstance(job_template, dict):
        return False, None, "spec.jobTemplate must be a dictionary"

    if not job_template.get("spec"):
        return False, None, "spec.jobTemplate.spec is required"

    return True, parsed, None


def _strip_immutable_fields(spec):
    spec.pop("status", None)
    metadata = spec.get("metadata", {})
    metadata.pop("uid", None)
    metadata.pop("resourceVersion", None)
    return spec


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


@app.route("/")
@app.route("/namespaces/")
@auth.login_required
def index():
    if config.NAMESPACE_ONLY:
        return redirect(
            f"/namespaces/{config.KRONIC_NAMESPACE}",
            code=302,
        )

    cronjobs = get_cronjobs()
    namespaces = {}
    # Count cronjobs per namespace
    for cronjob in cronjobs:
        namespaces[cronjob["namespace"]] = namespaces.get(cronjob["namespace"], 0) + 1

    return render_template("index.html", namespaces=namespaces)


@app.route("/namespaces/<namespace>")
@namespace_filter
@auth.login_required
def view_namespace(namespace):
    cronjobs = get_cronjobs(namespace)
    cronjobs_with_details = []
    all_pods = get_pods(namespace=namespace)

    for cronjob in cronjobs:
        cronjob_detail = get_cronjob(namespace, cronjob["name"])
        jobs = get_jobs(namespace=namespace, cronjob_name=cronjob["name"])
        for job in jobs:
            job["pods"] = [
                pod for pod in all_pods if pod_is_owned_by(pod, job["metadata"]["name"])
            ]
        cronjob_detail["jobs"] = jobs

        # Add interpreted schedule
        if (
            cronjob_detail
            and "spec" in cronjob_detail
            and "schedule" in cronjob_detail["spec"]
        ):
            cronjob_detail["interpreted_schedule"] = _interpret_cron_schedule(
                cronjob_detail["spec"]["schedule"]
            )
        else:
            cronjob_detail["interpreted_schedule"] = "Unknown schedule"

        cronjobs_with_details.append(cronjob_detail)

    return render_template(
        "namespace.html", cronjobs=cronjobs_with_details, namespace=namespace
    )


@app.route("/namespaces/<namespace>/cronjobs/<cronjob_name>", methods=["GET", "POST"])
@namespace_filter
@auth.login_required
def view_cronjob(namespace, cronjob_name):
    validation_error = None

    if request.method == "POST":
        yaml_content = request.form["yaml"]

        # Validate the YAML content
        is_valid, edited_cronjob, error_message = _validate_cronjob_yaml(yaml_content)

        if not is_valid:
            # If validation fails, show the error and return to edit page
            validation_error = error_message
            cronjob = get_cronjob(namespace, cronjob_name)
            if cronjob:
                cronjob = _strip_immutable_fields(cronjob)
            else:
                # Create default CronJob structure if none exists
                cronjob = {
                    "apiVersion": "batch/v1",
                    "kind": "CronJob",
                    "metadata": {"name": cronjob_name, "namespace": namespace},
                    "spec": {
                        "schedule": "*/10 * * * *",
                        "jobTemplate": {
                            "spec": {
                                "template": {
                                    "spec": {
                                        "containers": [
                                            {
                                                "name": "example",
                                                "image": "busybox:latest",
                                                "imagePullPolicy": "IfNotPresent",
                                                "command": [
                                                    "/bin/sh",
                                                    "-c",
                                                    "echo hello; date",
                                                ],
                                            }
                                        ],
                                        "restartPolicy": "OnFailure",
                                    }
                                }
                            }
                        },
                    },
                }
            # Return the user's input for editing
            return render_template(
                "cronjob.html",
                cronjob=cronjob,
                yaml=yaml_content,
                validation_error=validation_error,
            )

        # If validation passes, proceed with update
        cronjob = update_cronjob(namespace, edited_cronjob)

        # Check if the update failed (e.g., Kubernetes API error)
        if "error" in cronjob:
            validation_error = f"Kubernetes API error: {cronjob.get('exception', {}).get('message', 'Unknown error')}"
            # Get the original cronjob for fallback
            original_cronjob = get_cronjob(namespace, cronjob_name)
            if original_cronjob:
                original_cronjob = _strip_immutable_fields(original_cronjob)
            else:
                original_cronjob = edited_cronjob
            return render_template(
                "cronjob.html",
                cronjob=original_cronjob,
                yaml=yaml_content,
                validation_error=validation_error,
            )

        # If the name changed, redirect to the new cronjob
        if cronjob["metadata"]["name"] != cronjob_name:
            return redirect(
                f"/namespaces/{namespace}/cronjobs/{cronjob['metadata']['name']}",
                code=302,
            )
    else:
        cronjob = get_cronjob(namespace, cronjob_name)

    if cronjob:
        cronjob = _strip_immutable_fields(cronjob)
    else:
        cronjob = {
            "apiVersion": "batch/v1",
            "kind": "CronJob",
            "metadata": {"name": cronjob_name, "namespace": namespace},
            "spec": {
                "schedule": "*/10 * * * *",
                "jobTemplate": {
                    "spec": {
                        "template": {
                            "spec": {
                                "containers": [
                                    {
                                        "name": "example",
                                        "image": "busybox:latest",
                                        "imagePullPolicy": "IfNotPresent",
                                        "command": [
                                            "/bin/sh",
                                            "-c",
                                            "echo hello; date",
                                        ],
                                    }
                                ],
                                "restartPolicy": "OnFailure",
                            }
                        }
                    }
                },
            },
        }

    cronjob_yaml = yaml.dump(cronjob)
    return render_template(
        "cronjob.html",
        cronjob=cronjob,
        yaml=cronjob_yaml,
        validation_error=validation_error,
    )


@app.route("/api/")
@auth.login_required
def api_index():
    if config.NAMESPACE_ONLY:
        return redirect(
            f"/api/namespaces/{config.KRONIC_NAMESPACE}",
            code=302,
        )
    # Return all cronjobs
    jobs = get_cronjobs()
    return jobs


@app.route("/api/namespaces/<namespace>/cronjobs")
@app.route("/api/namespaces/<namespace>")
@namespace_filter
@auth.login_required
def api_namespace(namespace):
    cronjobs = get_cronjobs(namespace)
    return cronjobs


@app.route("/api/namespaces/<namespace>/cronjobs/<cronjob_name>")
@namespace_filter
@auth.login_required
def api_get_cronjob(namespace, cronjob_name):
    cronjob = get_cronjob(namespace, cronjob_name)
    return cronjob


@app.route(
    "/api/namespaces/<namespace>/cronjobs/<cronjob_name>/clone", methods=["POST"]
)
@namespace_filter
@auth.login_required
def api_clone_cronjob(namespace, cronjob_name):
    cronjob_spec = get_cronjob(namespace, cronjob_name)
    new_name = request.json["name"]
    cronjob_spec["metadata"]["name"] = new_name
    cronjob_spec["spec"]["jobTemplate"]["metadata"]["name"] = new_name
    cronjob_spec = _strip_immutable_fields(cronjob_spec)
    print(cronjob_spec)
    cronjob = update_cronjob(namespace, cronjob_spec)
    return cronjob


@app.route("/api/namespaces/<namespace>/cronjobs/create", methods=["POST"])
@namespace_filter
@auth.login_required
def api_create_cronjob(namespace):
    cronjob_spec = request.json["data"]
    cronjob = update_cronjob(namespace, cronjob_spec)
    return cronjob


@app.route(
    "/api/namespaces/<namespace>/cronjobs/<cronjob_name>/delete", methods=["POST"]
)
@namespace_filter
@auth.login_required
def api_delete_cronjob(namespace, cronjob_name):
    deleted = delete_cronjob(namespace, cronjob_name)
    return deleted


@app.route(
    "/api/namespaces/<namespace>/cronjobs/<cronjob_name>/suspend",
    methods=["GET", "POST"],
)
@namespace_filter
@auth.login_required
def api_toggle_cronjob_suspend(namespace, cronjob_name):
    if request.method == "GET":
        """Return the suspended status of the <cronjob_name>"""
        cronjob = get_cronjob(namespace, cronjob_name)
        return cronjob
    if request.method == "POST":
        """Toggle the suspended status of <cronjob_name>"""
        cronjob = toggle_cronjob_suspend(namespace, cronjob_name)
        return cronjob


@app.route(
    "/api/namespaces/<namespace>/cronjobs/<cronjob_name>/trigger", methods=["POST"]
)
@namespace_filter
@auth.login_required
def api_trigger_cronjob(namespace, cronjob_name):
    """Manually trigger a job from <cronjob_name>"""
    cronjob = trigger_cronjob(namespace, cronjob_name)
    status = 200
    if "error" in cronjob:
        status = cronjob["error"]

    return cronjob, status


@app.route("/api/namespaces/<namespace>/cronjobs/<cronjob_name>/getJobs")
@namespace_filter
@auth.login_required
def api_get_jobs(namespace, cronjob_name):
    jobs = get_jobs_and_pods(namespace, cronjob_name)
    return jobs


@app.route("/api/namespaces/<namespace>/pods")
@namespace_filter
@auth.login_required
def api_get_pods(namespace):
    pods = get_pods(namespace)
    return pods


@app.route("/api/namespaces/<namespace>/pods/<pod_name>/logs")
@namespace_filter
@auth.login_required
def api_get_pod_logs(namespace, pod_name):
    logs = get_pod_logs(namespace, pod_name)
    return logs


@app.route("/api/namespaces/<namespace>/jobs/<job_name>/delete", methods=["POST"])
@namespace_filter
@auth.login_required
def api_delete_job(namespace, job_name):
    deleted = delete_job(namespace, job_name)
    return deleted
