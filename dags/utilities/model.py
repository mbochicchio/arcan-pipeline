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

def parsing(id, date_parsing, project_version, status, file_result):
    return {
        'id': id,
        'date_parsing': date_parsing,
        'project_version': project_version,
        'status': status,
        'file_result': file_result
    }

def analysis(id, date_analysis, project_version, arcan_version, status, file_result):
    return {
        'id': id,
        'date_analysis': date_analysis,
        'project_version': project_version,
        'arcan_version': arcan_version,
        'status': status,
        'file_result': file_result
    }

def arcan_version(id, version, date_of_release):
    return {
        'id': id,
        'version': version,
        'date_of_release': date_of_release 
    }