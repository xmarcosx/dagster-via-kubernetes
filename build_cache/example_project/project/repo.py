from dagster import repository

from example_project.project.jobs.hello import hello_dagster


@repository
def dev_repo():
    return [hello_dagster]
