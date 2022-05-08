import os

from dagster import fs_io_manager, graph, job, multiprocess_executor, op
from dagster_gcp.gcs.io_manager import gcs_pickle_io_manager
from dagster_gcp.gcs.resources import gcs_resource


@op
def get_name():
    return "dagster"


@op
def hello(name: str):
    print(f"Hello, {name}!")


@graph
def hello_dagster():
    hello(get_name())


hello_dagster_dev_job = hello_dagster.to_job(
    executor_def=multiprocess_executor.configured({"max_concurrent": 8}),
    resource_defs={"gcs": gcs_resource, "io_manager": fs_io_manager},
)

hello_dagster_prod_job = hello_dagster.to_job(
    executor_def=multiprocess_executor.configured({"max_concurrent": 8}),
    resource_defs={
        "gcs": gcs_resource,
        "io_manager": gcs_pickle_io_manager.configured(
            {"gcs_bucket": "analog-medium-349613", "gcs_prefix": "dagster_io"}
        ),
    },
)
