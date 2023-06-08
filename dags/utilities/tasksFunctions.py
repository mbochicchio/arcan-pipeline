from utilities.mySqlGateway import MySqlGateway
from datetime import datetime
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
    if (len(version_list) == 0):
        last_commit = gitHubRepository.get_last_commit(project, last_version_analyzed)
        if (last_commit and ((not last_version_analyzed) or (last_version_analyzed['id_github'] != str(last_commit['id_github'])))):
            return [last_commit]
    else:
        number_of_version = len(version_list)
        if last_version_analyzed and (last_version_analyzed['id_github'] == version_list[number_of_version-1]['id_github']):
            version_list.pop()
        if (number_of_version != 0):
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
    
def create_version_directory(version: dict):
    gw = MySqlGateway()
    project = gw.get_project_by_id(version['project'])
    project_path = fileManager.get_version_path(version['id'])
    fileManager.create_dir(project_path)
    fileManager.clone_repository(project['name'], project_path)
    fileManager.checkout_repository(version=version['id_github'], project_dir=project_path)

def create_dependency_graph(version:dict, arcan_version:dict):
    gw = MySqlGateway()
    project = gw.get_project_by_id(version['project'])
    dockerRunner.execute_parsing(version_id=version['id'], project_language=project['language'], arcan_image=arcan_version['version'])
    output_path = fileManager.get_output_file_path(output_type="dependency-graph", version_id=version['id'])
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    dependency_graph = model.dependency_graph(None, now, output_path, version['id'])
    return dependency_graph

def create_analysis(version:dict, arcan_version:dict):
    gw = MySqlGateway()
    project = gw.get_project_by_id(version['project'])
    dockerRunner.execute_analysis(version_id=version['id'], project_language=project['language'], arcan_image=arcan_version['version'])
    output_file_path = fileManager.get_output_file_path(output_type="analysis", version_id=version['id'])
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

def delete_version_directory(version_id: dict):
    version_path = fileManager.get_version_path(version_id)
    output_parsing_path = fileManager.get_output_path(output_type="dependency-graph", version_id=version_id)
    output_analysis_path = fileManager.get_output_path(output_type="analysis", version_id=version_id)
    fileManager.delete_dir(path=version_path)
    fileManager.delete_dir(path=output_parsing_path)
    fileManager.delete_dir(path=output_analysis_path)  