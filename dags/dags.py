
import json

import pendulum

from airflow.decorators import dag, task

@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
)
def pipeline():

    @task()
    def get_project_list():
        project_list = ["progetto1", "progetto2", "progetto3"]
        return project_list
    
    @task()
    def select_version(project: str):
        version_list = ["versione1" + project, "versione2" + project]
        return version_list
    
    @task()
    def execute(version_list: list):
        for version in version_list:
            print(version)
        
    
    version_list = select_version.expand(project=get_project_list())
    execute.expand(version_list=version_list)

pipeline()
