def version(id, id_github, date, project):
    return {
      'id': id,
      'id_github': id_github,
      'date': date,
      'project': project
    }

def project(id, repository, language, name):
    return {
      'id': id,
      'repository': repository,
      'language': language,
      'name': name
    }      

def repository(id, project_repository, branch, username, password):
    return {
      'id': id,
      'project_repository': project_repository,
      'branch': branch,
      'username': username,
      'password': password
    }

def dependency_graph(id, date_parsing, file_result, project_version, is_completed):
    return {
        'id': id,
        'date_parsing': date_parsing,
        'file_result': file_result,
        'project_version': project_version,
        'is_completed': is_completed
    }

def analysis(id, date_analysis, file_result, project_version, arcan_version, is_completed):
    return {
        'id': id,
        'date_analysis': date_analysis,
        'file_result': file_result,
        'project_version': project_version,
        'arcan_version': arcan_version,
        'is_completed': is_completed
    }

def arcan_version(id, version, date_of_release):
    return {
        'id': id,
        'version': version,
        'date_of_release': date_of_release 
    }