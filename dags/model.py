def version(id, id_github, date, id_project):
    return {
      'id': id,
      'id_github': id_github,
      'date': date,
      'id_project': id_project,
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