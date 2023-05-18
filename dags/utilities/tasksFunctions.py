from utilities.mySqlGateway import MySqlGateway
from datetime import datetime
import math
from utilities import model, fileManager, dockerRunner, gitHubRepository, constants
from utilities.customException import ArcanOutputNotFoundException
import time

def get_project_list():
    gw = MySqlGateway()
    project_list = gw.get_projects_list()
    return project_list

#funzioni per inception

def get_last_version(project: dict):
    gw = MySqlGateway()
    return gw.get_last_version(project['id'])

def get_new_version_list(project:dict, last_version_analyzed:dict):
    version_list = gitHubRepository.get_version_list(project, last_version_analyzed)
    if (len(version_list) == 0):
        last_commit = gitHubRepository.get_last_commit(project)
        if (last_commit and ((not last_version_analyzed) or (last_version_analyzed['id_github'] != str(last_commit['id_github'])))):
            return [last_commit]
    else:
        number_of_version = len(version_list)
        if last_version_analyzed and (last_version_analyzed['id_github'] == version_list[number_of_version-1]['id_github']):
            version_list.pop()
        if (number_of_version != 0):
            max_number_of_version_to_consider = math.floor(6*math.log10(number_of_version+1))
            if max_number_of_version_to_consider < number_of_version:
                indices = [int(i * (number_of_version-1) / (max_number_of_version_to_consider-1)) for i in range(max_number_of_version_to_consider)]
                version_list = [version_list[i] for i in indices]
            return version_list

def save_new_project_versions(version_list: list):
    gw = MySqlGateway()
    if version_list:
        for version in reversed(version_list):
            gw.add_version(version)

def create_cross_dag_arguments(project_list: list):
    gw = MySqlGateway()
    arcan_version = gw.get_arcan_version()
    project_list_expanded=[]
    for project in project_list:
        version_list_for_project = gw.get_versions_list(project=project, arcan_version_id=arcan_version['id']) 
        project_list_expanded.append({constants.PROJECT: project, constants.VERSION_LIST: version_list_for_project})
    fileManager.create_cross_dag_arguments_file({constants.ARCAN_VERSION: arcan_version, constants.PROJECT_LIST:project_list_expanded})

def wait():
    time.sleep(60)

#funzioni per execution

def get_cross_dag_arguments():
    return fileManager.read_cross_dag_arguments_file()

def create_project_directory(project: dict):
    project_path = fileManager.get_project_path(project['id'])
    fileManager.create_dir(project_path)
    fileManager.clone_repository(project['name'], project_path)

def create_dependency_graph(version:dict):
    project_path = fileManager.get_project_path(version['project']['id'])
    fileManager.checkout_repository(version=version['id_github'], project_dir=project_path)
    dockerRunner.execute_parsing(project=version['project'])
    output_path = fileManager.get_output_file_path(output_type="dependency-graph", project_id=version['project']['id'])
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    dependency_graph = model.dependency_graph(None, now, output_path, version['id'])
    return dependency_graph

def create_analysis(version:dict, arcan_version:dict):
    project_path = fileManager.get_project_path(version['project']['id'])
    fileManager.checkout_repository(version=version['id_github'], project_dir=project_path)
    dockerRunner.execute_analysis(project=version['project'])
    output_file_path = fileManager.get_output_file_path(output_type="analysis", project_id=version['project']['id'])
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    analysis = model.analysis(None, now, output_file_path, version['id'], arcan_version['id'])
    return analysis

def save_dependency_graph(dependency_graph:dict):
    output_file_path = dependency_graph['file_result']
    dependency_graph['file_result'] = fileManager.get_blob_from_file(output_file_path)
    gw = MySqlGateway()
    gw.add_dependency_graph(dependency_graph)

def save_analysis(analysis:dict):
    file_result_path = analysis['file_result']
    analysis['file_result'] = fileManager.get_blob_from_file(file_result_path)
    gw = MySqlGateway()
    gw.add_analysis(analysis)

def delete_output_directory(project_id: str):
    output_parsing_path = fileManager.get_output_path(output_type="dependency-graph", project_id=project_id)
    output_analysis_path = fileManager.get_output_path(output_type="analysis", project_id=project_id)
    fileManager.delete_dir(path=output_parsing_path)
    fileManager.delete_dir(path=output_analysis_path)    
 
def delete_project_directory(project: dict):
    project_path = fileManager.get_project_path(project['id'])
    fileManager.delete_dir(path=project_path)