from dagster import repository

from project.jobs.hello import hello_dagster_dev_job, hello_dagster_prod_job


@repository
def development():
    return [hello_dagster_dev_job,]

@repository
def production():
    return [hello_dagster_prod_job]
