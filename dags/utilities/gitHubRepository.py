import requests
import json
from utilities import model
import threading
import time

ENDPOINT = "https://api.github.com"
PER_PAGE = 100

# Lock
lock = threading.Lock()
remaining_calls = None

# Funzione con accesso in mutua esclusione
def check_rate_limit():
    with lock:
        # Sezione critica
        global remaining_calls
        if not remaining_calls:
            initialize_rate_limit()
        if remaining_calls == 0:
            response_ok = False
            while not response_ok:
                response = requests.get('https://api.github.com/rate_limit')
                if response.status_code == 403 or response.status_code == 200:
                    response_ok = True
                    reset_time = float(response.headers['x-ratelimit-reset'])
                    wait_time = reset_time - time.time()
                    rate_limit = int(response.headers['x-ratelimit-limit'])
            if wait_time > 0:
                print(f'API rate limit exceeded: wait {wait_time} seconds')
                time.sleep(wait_time)
                remaining_calls = rate_limit       
        else:
            print(f'remaining_calls: {remaining_calls}')
            remaining_calls -= 1
        return True

def initialize_rate_limit():
    response_ok = False
    while not response_ok:
        response = requests.get('https://api.github.com/rate_limit')
        if response.status_code == 403 or response.status_code == 200:
            response_ok = True
            global remaining_calls
            remaining_calls = int(response.headers['x-ratelimit-remaining'])
            print(f'remaining_calls: {remaining_calls}')


def get_version_list(project: dict, last_version_analyzed: dict):
    complete = False
    page_number = 1
    version_list = []
    while (not complete):
        url = f"{ENDPOINT}/repos/{project['name']}/releases?page={page_number}&per_page={PER_PAGE}"
        #check_rate_limit()
        response = requests.get(url)
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
        #check_rate_limit()        
        response = requests.get(url)
        if response.status_code == 200:
            commit = json.loads(response.content)
            commit_parsed = model.version(None, commit['sha'], commit['commit']['committer']['date'], project['id'], None, None)
            complete = True
        elif response.status_code == 403:
            print("Git Rest API rate limit exceeded")
        else:
            raise Exception(f'API response: {response.status_code} with reason: {response.reason}')
    return commit_parsed
