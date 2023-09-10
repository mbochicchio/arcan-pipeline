from airflow.providers.mysql.hooks.mysql import MySqlHook
from typing import List, Tuple
from datetime import datetime
from utilities import model
from utilities.customException import SettingsException, ProjectNotFoundException

class MySqlGateway():
    def __init__(self):
        self.mysql_hook = MySqlHook(mysql_conn_id='mysql')
    
    def __execute_query__(self, sql: str, *args) -> List[Tuple]:
        with self.mysql_hook.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, args)
            return  cursor.fetchall()

    def __execute_transaction__(self, sql: str, data: Tuple) -> int:
        with self.mysql_hook.get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, data)
            id = cursor.lastrowid
            conn.commit()
            return id

    def get_project_by_id(self, project_id: int):
        sql = f"SELECT P.id, P.language, P.name, R.id, R.project_repository, R.branch, R.username, R.password FROM Project AS P JOIN Repository AS R ON P.id_repository = R.id WHERE P.id ={project_id}"
        myresult = self.__execute_query__(sql)
        if len(myresult) > 0:
            for item in myresult:
                return model.project(item[0], model.repository(item[3], item[4], item[5], item[6], item[7]), item[1], item[2])
        else:
            raise ProjectNotFoundException(f"Progetto {project_id} non trovato nel database")

    def get_projects_list(self, first_index, range):
        sql = f"SELECT P.id, P.language, P.name, R.id, R.project_repository, R.branch, R.username, R.password FROM Project AS P JOIN Repository AS R ON P.id_repository = R.id WHERE P.id >= {first_index} ORDER BY P.id ASC LIMIT {range}"
        myresult = self.__execute_query__(sql)
        project_list = []
        if len(myresult) > 0:
            for item in myresult:
                project_list.append(model.project(item[0], model.repository(item[3], item[4], item[5], item[6], item[7]), item[1], item[2]))
            return project_list
        else:
            raise SettingsException("Lista progetti vuota")

    def get_setting_by_name(self, name: str):
        sql = f"SELECT value FROM Settings WHERE name='{name}'"
        myresult = self.__execute_query__(sql)
        if len(myresult) > 0:
            return myresult[0][0]
        else:
            raise SettingsException(f"Setting {name} non trovata")
        
    def update_setting_by_name(self, name: str, value: str):
        sql = "UPDATE Settings SET value=%s WHERE name=%s"
        data = (value, name)
        self.__execute_transaction__(sql, data)

    def get_last_version(self, id_project: int):
        sql = f"SELECT * FROM Version WHERE id_project={id_project} ORDER BY id DESC LIMIT 0, 1"
        myresult = self.__execute_query__(sql)
        if len(myresult) > 0:
            return model.version(myresult[0][0], myresult[0][1], str(myresult[0][2]), myresult[0][3])
        else:
            return None
    
    def get_arcan_version(self):
        sql = "SELECT id, date_of_release, version FROM ArcanVersion ORDER BY date_of_release DESC LIMIT 0, 1"
        myresult = self.__execute_query__(sql)
        if len(myresult) > 0:
            return model.arcan_version(myresult[0][0], myresult[0][2], str(myresult[0][1]))
        else:
            raise SettingsException("Versione di Arcan non trovata")

    def get_versions_list(self, arcan_version_id: str, limit: int):
        sql = f"SELECT T.id, T.id_github, T.date, T.id_project FROM (SELECT DISTINCT * FROM Version AS V WHERE NOT EXISTS ( SELECT * FROM Analysis as A2 WHERE A2.project_version = V.id AND A2.arcan_version = {arcan_version_id}) LIMIT {limit}) AS T"
        myresult = self.__execute_query__(sql)
        version_list = []
        if len(myresult) > 0:
            for item in myresult:
                version_list.append(model.version(item[0], item[1], str(item[2]), item[3]))
            return version_list
        else:
            raise SettingsException("Lista versioni vuota")

    def get_dependency_graph_by_version_id(self, version_id: str):
        sql = f"SELECT file_result FROM DependencyGraph WHERE id = (SELECT file_result FROM Parsing WHERE project_version = {version_id} AND status='Successful' ORDER BY id DESC LIMIT 0, 1)"
        myresult = self.__execute_query__(sql)
        if len(myresult) > 0:
            return myresult[0][0]
        else:
            return None
        
    def add_version(self, version: dict):
        sql = "INSERT INTO Version (id_github, date, id_project) VALUES (%s, %s, %s)"
        data = (version['id_github'], datetime.strptime(version['date'], "%Y-%m-%dT%H:%M:%SZ"), version['project'])
        self.__execute_transaction__(sql, data)

    def add_project(self, project: dict):
        sql = "INSERT INTO Project (id_repository, language, name) VALUES (%s, %s, %s)"
        data = (project['id_repository'], project['language'], project['name'])
        self.__execute_transaction__(sql, data)

    def add_repository(self, repository: dict):
        sql = "INSERT INTO Repository (url_github, branch, username, password) VALUES (%s, %s, %s, %s)"
        data = (repository['url_github'], repository['branch'], repository['username'], repository['password'])
        self.__execute_transaction__(sql, data)

    def add_parsing(self, parsing: dict):
        sql = "INSERT INTO Parsing (date_parsing, project_version, status, file_result) VALUES (%s, %s, %s, %s)"
        data = (datetime.strptime(parsing['date_parsing'], "%Y-%m-%dT%H:%M:%SZ"), parsing['project_version'], parsing['status'], parsing['file_result'])
        self.__execute_transaction__(sql, data)

    def add_analysis(self, analysis:dict):
        sql = "INSERT INTO Analysis (date_analysis, project_version, arcan_version, status, file_result) VALUES (%s, %s, %s, %s, %s)"
        data = (datetime.strptime(analysis['date_analysis'], "%Y-%m-%dT%H:%M:%SZ"), analysis['project_version'], analysis['arcan_version'], analysis['status'], analysis['file_result'])
        self.__execute_transaction__(sql, data)

    def add_dependency_graph(self, blob):
        sql = "INSERT INTO DependencyGraph (file_result) VALUES (%s)"
        data = (blob)
        dependency_graph_id = self.__execute_transaction__(sql, data)
        return dependency_graph_id

    def add_analysis_result(self, blob):
        sql = "INSERT INTO AnalysisResult (file_result) VALUES (%s)"
        data = (blob)
        analysis_result_id = self.__execute_transaction__(sql, data)
        return analysis_result_id