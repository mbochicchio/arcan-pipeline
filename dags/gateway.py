from airflow.providers.mysql.hooks.mysql import MySqlHook
from typing import List, Tuple
from datetime import datetime
import model

class MySqlGateway():
    def __init__(self):
        self.mysql_hook = MySqlHook(mysql_conn_id='mysql')
    
    def __execute_query__(self, sql: str, *args) -> List[Tuple]:
        with self.mysql_hook.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, args)
            return  cursor.fetchall()

    def __execute_transaction__(self, sql: str, data: Tuple) -> bool:
        with self.mysql_hook.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, data)
            conn.commit()
            return True

    def get_projects_list(self):
        sql = "SELECT P.id, P.language, P.name, R.id, R.project_repository, R.branch, R.username, R.password FROM Project AS P JOIN Repository AS R ON P.id_repository = R.id"
        myresult = self.__execute_query__(sql)
        project_list = []
        if len(myresult) > 0:
            for item in myresult:
                project_list.append(model.project(item[0], model.repository(item[3], item[4], item[5], item[6], item[7]), item[1], item[2]))
        return project_list

    def get_last_version(self, id_project: int):
        sql = "SELECT * FROM Version WHERE id_project=" + str(id_project) + " ORDER BY id DESC LIMIT 0, 1"
        myresult = self.__execute_query__(sql)
        if len(myresult) > 0:
            return model.version(myresult[0][0], myresult[0][1], myresult[0][2], myresult[0][3])
        else:
            return None

    def add_version(self, version: dict):
        sql = "INSERT INTO Version (id_github, date, id_project) VALUES (%s, %s, %s)"
        data = (version['id_github'], datetime.strptime(version['date'], "%Y-%m-%dT%H:%M:%SZ"), version['id_project'])
        self.__execute_transaction__(sql, data)

    def add_project(self, project: dict):
        sql = "INSERT INTO Project (id_repository, language, name) VALUES (%s, %s, %s)"
        data = (project['id_repository'], project['language'], project['name'])
        self.__execute_transaction__(sql, data)

    def add_repository(self, repository: dict):
        sql = "INSERT INTO Repository (url_github, branch, username, password) VALUES (%s, %s, %s, %s)"
        data = (repository['url_github'], repository['branch'], repository['username'], repository['password'])
        self.__execute_transaction__(sql, data)
