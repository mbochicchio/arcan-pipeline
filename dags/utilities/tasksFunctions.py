from utilities.mySqlGateway import MySqlGateway
import datetime
import pytz
from math import floor, log10
from utilities import model, fileManager, dockerRunner, gitHubRepository

def get_project_list(project_range: dict):
    gw = MySqlGateway()
    project_list = gw.get_projects_list(first_index = project_range['first_index'], range = project_range['range'])
    return project_list

def get_arcan_version():
    gw = MySqlGateway()
    return gw.get_arcan_version()

def update_project_range(project_range:dict, number_of_projects_considered: int):
    gw = MySqlGateway()
    if number_of_projects_considered < project_range['range']:
        new_index = 1
    else:
        new_index = project_range['first_index'] + project_range['range']
    gw.update_setting_by_name('first_index_inception',str(new_index))

def get_project_range():
    gw = MySqlGateway()
    range = int(gw.get_setting_by_name('inception_range'))
    first_index = int(gw.get_setting_by_name('first_index_inception'))
    settings = {'range': range, 'first_index': first_index}
    return settings

def get_version_range():
    gw = MySqlGateway()
    return int(gw.get_setting_by_name('execution_range'))

def get_last_version(project: dict):
    gw = MySqlGateway()
    return gw.get_last_version(project['id'])

def get_new_version_list(project:dict, last_version_analyzed:dict):
    version_list = gitHubRepository.get_version_list(project, last_version_analyzed)
    number_of_version = len(version_list)
    if (number_of_version == 0):
        last_commit = gitHubRepository.get_last_commit(project)
        if (last_commit and ((not last_version_analyzed) or ((datetime.datetime.strptime(last_commit['date'], "%Y-%m-%dT%H:%M:%SZ") - datetime.datetime.strptime(last_version_analyzed['date'], "%Y-%m-%d %H:%M:%S")).days > 30 ))):
            return [last_commit]
    else:
        if last_version_analyzed and (datetime.datetime.strptime(version_list[number_of_version-1]['date'], "%Y-%m-%dT%H:%M:%SZ") <= datetime.datetime.strptime(last_version_analyzed['date'], "%Y-%m-%d %H:%M:%S")):
            version_list.pop()
            number_of_version -= 1
        if (number_of_version > 0):
            max_number_of_version_to_consider = floor(6*log10(number_of_version+1))
            if max_number_of_version_to_consider < number_of_version:
                indices = [int(i * (number_of_version-1) / (max_number_of_version_to_consider-1)) for i in range(max_number_of_version_to_consider)]
                version_list = [version_list[i] for i in indices]
            return version_list

def save_new_project_versions(version_list: list):
    gw = MySqlGateway()
    if version_list:
        for version in reversed(version_list):
            gw.add_version(version)

def get_version_list(version_range: int, arcan_version:dict):
    gw = MySqlGateway()
    return gw.get_versions_list(limit=version_range, arcan_version_id=arcan_version['id'])
    
def create_version_directory(version: dict, project: dict):
    version_directory = fileManager.get_version_directory(version['id'])
    fileManager.create_dir(version_directory)
    fileManager.clone_repository(project['name'], version_directory)
    fileManager.checkout_repository(version=version['id_github'], version_directory=version_directory)

def get_project_by_id(project_id: int):
    gw = MySqlGateway()
    return gw.get_project_by_id(project_id)

def create_dependency_graph(version:dict, project:dict, arcan_version:dict):
    dockerRunner.execute_parsing(version_id=version['id'], project_language=project['language'], arcan_image=arcan_version['version'])
    output_file = fileManager.get_output_file_path(output_type="dependency-graph", version_id=version['id'])
    return output_file

def get_dependency_graph(version: dict):
    gw = MySqlGateway()
    dependency_graph_blob = gw.get_dependency_graph_by_version_id(version['id'])
    if dependency_graph_blob:
        output_directory = fileManager.get_output_directory(output_type="dependency-graph", version_id=version['id'])
        fileManager.create_dir(path=output_directory)
        output_file = fileManager.write_file(data=dependency_graph_blob, path=output_directory)
        return output_file
    else:
        return None

def save_dependency_graph(output_file_path: str):
    blob = fileManager.get_blob_from_file(output_file_path)
    gw = MySqlGateway()
    id_dependency_graph = gw.add_dependency_graph(blob)
    return id_dependency_graph

def save_parsing(version: dict, status="SUCCESSFUL", dependency_graph=None):
    now = datetime.datetime.now(pytz.timezone('Europe/Rome')).strftime("%Y-%m-%dT%H:%M:%SZ")
    parsing = model.parsing(None, now, version['id'], status, dependency_graph)
    gw = MySqlGateway()
    gw.add_parsing(parsing)

def create_analysis(version:dict, project:dict, arcan_version:dict, dependency_graph_local_path:str):
    dependency_graph_container_path = fileManager.get_dependency_graph_container_path(dependency_graph_local_path)
    dockerRunner.execute_analysis(version=version, project_language=project['language'], arcan_image=arcan_version['version'], dependency_graph=dependency_graph_container_path)
    output_file_path = fileManager.get_output_file_path(output_type="analysis", version_id=version['id'])
    return output_file_path

def save_analysis_result(output_file_path: str):
    blob = fileManager.get_blob_from_file(output_file_path)
    gw = MySqlGateway()
    id_analysis_result = gw.add_analysis_result(blob)
    return id_analysis_result

def save_analysis(version: dict, arcan_version: dict, status="SUCCESSFUL", analysis_result=None):
    now = datetime.datetime.now(pytz.timezone('Europe/Rome')).strftime("%Y-%m-%dT%H:%M:%SZ")
    analysis = model.analysis(None, now, version['id'], arcan_version['id'], status, analysis_result)
    gw = MySqlGateway()
    gw.add_analysis(analysis)

def delete_version_directory(version_id: dict):
    version_path = fileManager.get_version_directory(version_id)
    output_parsing_path = fileManager.get_output_directory(output_type="dependency-graph", version_id=version_id)
    output_analysis_path = fileManager.get_output_directory(output_type="analysis", version_id=version_id)
    fileManager.delete_dir(path=version_path)
    fileManager.delete_dir(path=output_parsing_path)
    fileManager.delete_dir(path=output_analysis_path)  