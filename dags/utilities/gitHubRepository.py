import json
from utilities import model
from utilities.customException import GitRestApiProjectNotFoundException, GitRestApiException, GitRestApiValidationFailedException
import requests
import time
from airflow.models import Variable

ENDPOINT = "https://api.github.com"
PER_PAGE = 100
auth = ( Variable.get('git_username'),  Variable.get('git_token'))

def get_version_list(project: dict, last_version_analyzed: dict):
    complete = False
    page_number = 1
    version_list = []
    while (not complete):
        url = f"{ENDPOINT}/repos/{project['name']}/releases?page={page_number}&per_page={PER_PAGE}"
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            response_release_list = json.loads(response.content)
            for item in response_release_list:
                item_parsed = model.version(None, item['tag_name'], item['published_at'], project['id'], None, None)
                version_list.append(item_parsed)
                if last_version_analyzed and (last_version_analyzed['id_github'] == str(item_parsed['id_github'])):
                    complete = True
                    break
            if len(response_release_list) >= PER_PAGE and page_number < 10: #github impone di ottenere massimo 1000 release
                page_number += 1
            else:
                complete = True
        elif response.status_code == 403:
            wait_reset_time(float(response.headers['x-ratelimit-reset']))
        elif response.status_code == 404:
            raise GitRestApiProjectNotFoundException("The GitHub repository doesn't exist")
        else:
            raise GitRestApiException(f'API response: {response.status_code} with reason: {response.reason}')
    return version_list

def get_last_commit(project: dict):
    url = f"{ENDPOINT}/repos/{project['name']}/commits/{project['repository']['branch']}"
    complete = False
    while (not complete):
        response = requests.get(url, auth=auth)
        if response.status_code == 200:
            commit = json.loads(response.content)
            commit_parsed = model.version(None, commit['sha'], commit['commit']['committer']['date'], project['id'], None, None)
            complete = True
        elif response.status_code == 403:
            wait_reset_time(float(response.headers['x-ratelimit-reset']))
        elif response.status_code == 404:
            raise GitRestApiProjectNotFoundException("The GitHub repository doesn't exist")
        elif response.status_code == 422:
            raise GitRestApiValidationFailedException("Validation failed, or the endpoint has been spammed")
        else:
            raise GitRestApiException(f'API response: {response.status_code} with reason: {response.text}')
    return commit_parsed

def wait_reset_time(reset_time: float):
    wait_time = reset_time - time.time()
    if wait_time > 0:
        print(f'API rate limit exceeded: wait {wait_time} seconds. Resume at {reset_time}')
        time.sleep(wait_time)
