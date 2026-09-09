from typing import Optional, List, Dict, Any, Literal
from langchain_core.tools import tool
import digitalhub as dh

PythonVersion = Literal["PYTHON3_10", "PYTHON3_11", "PYTHON3_12", "PYTHON3_13"]


@tool
def new_dh_python_function(
    project: str,
    name: str,
    handler: str,
    python_version: PythonVersion = "PYTHON3_10",
    code_src: Optional[str] = None,
    code: Optional[str] = None,
    base64: Optional[str] = None,
    init_function: Optional[str] = None,
    lang: Optional[str] = None,
    image: Optional[str] = None,
    base_image: Optional[str] = None,
    requirements: Optional[List[str]] = None,
    uuid: Optional[str] = None,
    description: Optional[str] = None,
    labels: Optional[List[str]] = None,
    embedded: bool = False,
):
    """
    Create a Function of kind='python' with the Python-runtime spec.
    Provide exactly one of 'code_src' (URI to source), 'code' (source text),
    or 'base64' (base64-encoded source). 'handler' is the entrypoint (e.g. 'main').
    'python_version' must be one of PYTHON3_10..PYTHON3_13.
    'requirements' is a list of pip specifiers (e.g. ['numpy', 'pandas>1,<3']).
    """
    return dh.new_function(
        project=project,
        name=name,
        kind="python",
        uuid=uuid,
        description=description,
        labels=labels,
        embedded=embedded,
        handler=handler,
        python_version=python_version,
        code_src=code_src,
        code=code,
        base64=base64,
        init_function=init_function,
        lang=lang,
        image=image,
        base_image=base_image,
        requirements=requirements,
    )


@tool
def run_dh_python_job(
    project_name: str,
    name: str,
    local_execution: bool = False,
    inputs: Optional[dict] = None,
    parameters: Optional[dict] = None,
    init_parameters: Optional[dict] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Execute a Python function as a one-off job (action='job').
    'inputs' maps handler argument names to entity keys (Dataitem/Artifact/Model).
    'parameters' are plain Python values passed to the handler.
    'init_parameters' are values passed to the init function (remote execution).
    Set 'local_execution=True' to run on the local machine instead of the cluster.
    """
    func = dh.get_function(name, project=project_name)
    return func.run(
        action="job",
        wait=wait,
        log_info=log_info,
        local_execution=local_execution,
        inputs=inputs,
        parameters=parameters,
        init_parameters=init_parameters,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


@tool
def run_dh_python_serve(
    project_name: str,
    name: str,
    inputs: Optional[dict] = None,
    parameters: Optional[dict] = None,
    init_parameters: Optional[dict] = None,
    replicas: Optional[int] = None,
    service_type: Optional[str] = None,
    service_name: Optional[str] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Deploy a Python function as an HTTP service (action='serve').
    Serve is remote-only. After the run reaches a ready state, use
    invoke_dh_run_service to call the endpoint.
    """
    func = dh.get_function(name, project=project_name)
    return func.run(
        action="serve",
        wait=wait,
        log_info=log_info,
        inputs=inputs,
        parameters=parameters,
        init_parameters=init_parameters,
        replicas=replicas,
        service_type=service_type,
        service_name=service_name,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


@tool
def run_dh_python_build(
    project_name: str,
    name: str,
    instructions: Optional[List[str]] = None,
    inputs: Optional[dict] = None,
    parameters: Optional[dict] = None,
    init_parameters: Optional[dict] = None,
    volumes: Optional[List[dict]] = None,
    resources: Optional[dict] = None,
    envs: Optional[List[dict]] = None,
    secrets: Optional[List[str]] = None,
    profile: Optional[str] = None,
    wait: bool = True,
    log_info: bool = True,
):
    """
    Build a container image for a Python function (action='build').
    'instructions' are executed as RUN lines in the generated Dockerfile
    (e.g. ["apt-get install -y git"]).
    """
    func = dh.get_function(name, project=project_name)
    return func.run(
        action="build",
        wait=wait,
        log_info=log_info,
        instructions=instructions,
        inputs=inputs,
        parameters=parameters,
        init_parameters=init_parameters,
        volumes=volumes,
        resources=resources,
        envs=envs,
        secrets=secrets,
        profile=profile,
    )


PYTHON_RUNTIME_TOOLS = [
    new_dh_python_function,
    run_dh_python_job,
    run_dh_python_serve,
    run_dh_python_build,
]
