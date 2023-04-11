import mysql.connector
import model
from datetime import datetime


mydb = mysql.connector.connect(
  host="mysql",
  user="root",
  database="database"
)
mycursor = mydb.cursor()

def get_projects_list():
  mycursor.execute("SELECT P.id, P.language, P.name, R.id, R.project_repository, R.branch, R.username, R.password FROM Project AS P JOIN Repository AS R ON P.id_repository = R.id")
  myresult = mycursor.fetchall()
  project_list = []
  if len(myresult) > 0:
    for item in myresult:
      project_list.append(model.project(item[0], model.repository(item[3], item[4], item[5], item[6], item[7]), item[1], item[2]))
    return project_list
  return project_list

def get_last_version(id_project: int):
  mycursor.execute("SELECT * FROM Version WHERE id_project=" + str(id_project) + " ORDER BY id DESC LIMIT 0, 1")
  myresult = mycursor.fetchall()
  if len(myresult) > 0:
    return model.version(myresult[0][0], myresult[0][1], myresult[0][2], myresult[0][3])
  else:
    return None

def add_version(version: dict):
  sql = "INSERT INTO Version (id_github, date, id_project) VALUES (%s, %s, %s)"
  val = (version['id_github'], datetime.strptime(version['date'], "%Y-%m-%dT%H:%M:%SZ"), version['id_project'])
  add_execute(sql, val)

def add_project(project: dict):
  sql = "INSERT INTO Project (id_repository, language, name) VALUES (%s, %s, %s)"
  val = (project['id_repository'], project['language'], project['name'])
  add_execute(sql, val)

def add_repository(repository: dict):
  sql = "INSERT INTO Repository (url_github, branch, username, password) VALUES (%s, %s, %s, %s)"
  val = (repository['url_github'], repository['branch'], repository['username'], repository['password'])
  add_execute(sql, val)

def add_project_repository(project: dict, repository: dict):
  add_repository(repository=repository)
  project.repository=mycursor.lastrowid
  add_project(project=project)

def add_execute(sql: str, val = list):
  mycursor.execute(sql, val)
  mydb.commit()
