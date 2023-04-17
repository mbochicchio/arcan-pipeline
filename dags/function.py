from gateway import MySqlGateway
import gitHubRepository
from datetime import datetime
import math
import model


def get_project_list():
    gw = MySqlGateway()
    project_list = gw.get_projects_list()
    return project_list

def get_arcan_version():
    gw = MySqlGateway()
    arcan_version = gw.get_arcan_version()
    return arcan_version

def add_project_versions(project: dict):
    gw = MySqlGateway()
    last_version_analyzed = gw.get_last_version(project['id'])
    version_list = gitHubRepository.get_version_list(project)

    if (len(version_list) == 0):
        last_commit = gitHubRepository.get_last_commit(project)
        if (last_commit and ((not last_version_analyzed) or (last_version_analyzed['id_github'] != str(last_commit['id_github'])))):
            gw.add_version(last_commit)
    else:
        if last_version_analyzed:
            index = 0
            if (last_version_analyzed['id_github'] != str(version_list[0]['id_github'])):
                find = False
                len_version_list = len(version_list)
                while index < len_version_list and not find:
                    if str(version_list[0]['id_github']) == last_version_analyzed['id_github']:
                        find = True
                    index +=1
            version_list = version_list[:index]
        
        number_of_version = len(version_list)
        if (number_of_version != 0):
            max_number_of_version_to_consider = math.floor(6*math.log10(number_of_version+1))
            step = math.ceil(number_of_version / max_number_of_version_to_consider)
            version_list = version_list[::step]
            version_list.reverse()
            for item in version_list:
                gw.add_version(item)

def get_version_list(project: dict, arcan_version:dict):
    gw = MySqlGateway()
    version_list = gw.get_versions_list(project=project, arcan_version=arcan_version) 
    return version_list

def create_dependency_graph(version:dict):
    gw = MySqlGateway()
    now = datetime.strptime(datetime.now(), "%Y-%m-%dT%H:%M:%SZ")
    dependency_graph = model.dependency_graph(None, now, None, version['id'])
    gw.add_dependency_graph(dependency_graph)

def analyze_version(version:dict, arcan_version:dict):
    gw = MySqlGateway()
    now = datetime.strptime(datetime.now(), "%Y-%m-%dT%H:%M:%SZ")
    analyzis = model.analysis(None, now, None, version['id'], arcan_version['id'])
    gw.add_analysis(analyzis)