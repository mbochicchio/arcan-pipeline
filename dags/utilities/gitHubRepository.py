import requests
import json
from utilities import model
from ratelimit import limits, sleep_and_retry

NUMBER_CALLS = 60 
PERIOD = 3610 #60 minuti con 10 secondi di precauzione
PER_PAGE = 100
ENDPOINT = "https://api.github.com"

@sleep_and_retry
@limits(calls=NUMBER_CALLS, period=PERIOD)
def api_request(url):
    return requests.get(url)

def get_version_list(project: dict, last_version_analyzed: dict):
    complete = False
    page_number = 1
    version_list = []
    while (not complete):
        url = f"{ENDPOINT}/repos/{project['name']}/releases?page={page_number}&per_page={PER_PAGE}"
        response = api_request(url)
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
            print("Git Rest API rate limit exceeded")
        else:
            raise Exception(f'API response: {response.status_code} with reason: {response.reason}')
    return version_list

def get_last_commit(project: dict):
    url = f"{ENDPOINT}/repos/{project['name']}/commits/{project['repository']['branch']}"
    complete = False
    while (not complete):
        response= api_request(url)
        if response.status_code == 200:
            commit = json.loads(response.content)
            commit_parsed = model.version(None, commit['sha'], commit['commit']['committer']['date'], project['id'], None, None)
            complete = True
        elif response.status_code == 403:
            print("Git Rest API rate limit exceeded")
        else:
            raise Exception(f'API response: {response.status_code} with reason: {response.reason}')
    return commit_parsed
