import pendulum
from airflow.decorators import dag, task
from utilitis import function

@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
)
def inception():

    @task()
    def get_project_list():
        project_list = function.get_project_list()
        return project_list
    
    @task()
    def add_project_versions(project: dict):
        function.add_project_versions(project)

    project_list=get_project_list()
    add_project_versions.expand(project=project_list)
 
inception()
