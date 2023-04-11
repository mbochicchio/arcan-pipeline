import pendulum
from airflow.decorators import dag, task
import mySqlRepository
import function

@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=[],
)
def pipeline():

    @task()
    def get_project_list():
        project_list = mySqlRepository.get_projects_list()
        return project_list
    
    @task()
    def filter_project_versions(project: dict):
        function.filter_project_versions(project)

    filter_project_versions.expand(project=get_project_list())

pipeline()
