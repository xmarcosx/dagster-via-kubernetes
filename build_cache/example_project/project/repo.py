from dagster import repository

from jobs.hello import hello_dagster


@repository
def dev_repo():
    return [hello_dagster]
