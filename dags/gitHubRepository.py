import requests
import json
import model

base_url = "https://api.github.com"

def get_version_list(project: dict):
    url = f"{base_url}/repos/{project['name']}/releases"
    response = requests.get(url)
    if response.status_code == 200:
        version_list_filtered = []
        version_list = json.loads(response.content)
        for item in version_list:
            item_filtered = model.version(None, item['tag_name'], item['published_at'], project['id'])
            version_list_filtered.append(item_filtered)
    return version_list_filtered

def get_last_commit(project: dict):
    url = f"{base_url}/repos/{project['name']}/commits/{project['repository']['branch']}"
    response = requests.get(url)
    if response.status_code == 200:
        commit = json.loads(response.content)
        commit_filtered = model.version(None, commit['sha'], commit['commit']['committer']['date'], project['id'])
    return commit_filtered
