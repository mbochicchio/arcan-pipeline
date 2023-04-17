def version(id, id_github, date, id_project, last_analysis, dependency_graph):
    return {
      'id': id,
      'id_github': id_github,
      'date': date,
      'id_project': id_project,
      'last_analysis': last_analysis,
      'dependency_graph': dependency_graph
    }

def project(id, repository, language, name):
    return {
      'id': id,
      'repository': repository,
      'language': language,
      'name': name,
    }      

def repository(id, project_repository, branch, username, password):
    return {
      'id': id,
      'project_repository': project_repository,
      'branch': branch,
      'username': username,
      'password': password
    }

def dependency_graph(id, date_parsing, file_result, project_version):
    return {
        'id': id,
        'date_parsing': date_parsing,
        'file_result': file_result,
        'project_version': project_version
    }

def analysis(id, date_analysis, file_result, project_version, arcan_version):
    return {
        'id': id,
        'date_analysis': date_analysis,
        'file_result': file_result,
        'project_version': project_version,
        'arcan_version': arcan_version
    }

def arcan_version(id, version, date_of_release):
    return {
        'id': id,
        'version': version,
        'date_of_release': date_of_release 
    }