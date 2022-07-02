import json
import logging
import os
import requests

from dotenv import load_dotenv

load_dotenv()
TARGET_NEXUS_URL = os.environ.get("TARGET_NEXUS_URL")
SOURCE_NEXUS_URL = os.environ.get("SOURCE_NEXUS_URL")
REPO_TYPE = os.environ.get("REPO_TYPE")
REPO_FORMAT = os.environ.get("REPO_FORMAT")
DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR")
SOURCE_NEXUS_USER = os.environ.get("SOURCE_NEXUS_USER")
SOURCE_NEXUS_PASS = os.environ.get("SOURCE_NEXUS_PASS")
TARGET_NEXUS_USER = os.environ.get("TARGET_NEXUS_USER")
TARGET_NEXUS_PASS = os.environ.get("TARGET_NEXUS_PASS")
FULL = os.environ.get("FULL")
REPO_FORMAT_URL = os.environ.get("REPO_FORMAT_URL")

logging.basicConfig(filename=os.path.dirname(os.path.abspath(__file__)) + "/logs/log.log",
                    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    level=logging.INFO
                    )


def create_download_dir() -> None:
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)


def get_repositories_from_nexus(url, login: str, password: str) -> list:
    repositories = []
    response = requests.get(url + '/service/rest/v1/repositories', auth=(login, password))
    for repo in response.json():
        if repo['type'] == REPO_TYPE and repo['format'] == REPO_FORMAT:
            repositories.append(repo['name'])
    return repositories


def get_repositories_from_download_dir() -> list:
    repositories = []
    for filename in os.listdir(DOWNLOAD_DIR):
        repositories.append(filename)
    return repositories


def create_repo(name: str) -> None:
    data = get_body_for_repo_hosted(name)
    if len(data) == 0:
        print('Создание репозитория данного формата не поддерживается API. name: ' + name)
        return
    url = TARGET_NEXUS_URL + "/service/rest/v1/repositories/" + REPO_FORMAT_URL + "/" + REPO_TYPE
    response = requests.post(
        url,
        data=json.dumps(data),
        headers={'Content-type': 'application/json'},
        auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS)
    )
    if response.status_code > 404:
        logging.error("Creating repositories - " + name + " error: " + response.text)


def progress(count, total, status='') -> None:
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    print('[%s] %s%s ...%s\r' % (bar, percents, '%', status))


def get_all_assets(url: str, repo: str, login: str, password: str) -> dict:
    url_repo = url + "/service/rest/v1/search/assets?sort=name&repository=" + repo
    response = requests.get(url_repo, auth=(login, password))
    assets = response.json()["items"]
    token = ""
    if "continuationToken" in response.json():
        token = response.json()["continuationToken"]

    while token is not None:
        print("token: " + token)
        url = url_repo + "&continuationToken=" + token
        response = requests.get(url, auth=(login, password))
        if response.status_code > 400:
            logging.info("break")
            logging.info(response.status_code)
            logging.info(response.text)
            logging.info(response)
            break

        assets.extend(response.json()['items'])
        token = ""
        if "continuationToken" in response.json():
            token = response.json()["continuationToken"]
    return assets


def download_asset(asset: dict) -> None:
    arr_path = asset["path"].split("/")
    if len(arr_path) == 1:
        path_dir = ""
        file_name = asset["path"]
    else:
        file_name = asset["path"].split("/")[len(arr_path) - 1]
        path_dir = "/".join(arr_path[:-1])

    target_dir = DOWNLOAD_DIR + "/" + asset["repository"] + "/" + path_dir

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if not os.path.isfile(target_dir + "/" + file_name):
        with open(target_dir + "/" + file_name, "wb") as file:
            response = requests.get(asset["downloadUrl"], auth=(SOURCE_NEXUS_USER, SOURCE_NEXUS_PASS))
            file.write(response.content)


def search_diff() -> None:
    diffs = []
    source_repos = get_repositories_from_nexus(SOURCE_NEXUS_URL, SOURCE_NEXUS_USER, SOURCE_NEXUS_PASS)
    target_repos = get_repositories_from_nexus(TARGET_NEXUS_URL, TARGET_NEXUS_USER, TARGET_NEXUS_PASS)
    total = len(source_repos)
    progress_index = 0
    for repo in source_repos:
        progress(progress_index, total, status='searching diffs in ' + repo)
        source_assets = get_all_assets(SOURCE_NEXUS_URL, repo, SOURCE_NEXUS_USER, SOURCE_NEXUS_PASS)
        target_assets = get_all_assets(TARGET_NEXUS_URL, repo, TARGET_NEXUS_USER, TARGET_NEXUS_PASS)
        if len(source_assets) == 0:
            progress_index += 1
            continue
        if repo in target_repos:
            for src_asset in source_assets.copy():
                for t_asset in target_assets.copy():
                    if t_asset["path"] == src_asset["path"] or \
                            t_asset['checksum']['sha1'] == src_asset["checksum"]['sha1']:
                        if src_asset in source_assets:
                            source_assets.remove(src_asset)
                        if t_asset in target_assets:
                            target_assets.remove(t_asset)
                        break
            if len(source_assets) > 0:
                diffs.append({repo: source_assets})
        else:
            diffs.append({repo: "not found"})
        progress_index += 1
    progress(progress_index, total, status='searching diffs - Done')
    if len(diffs) > 0:
        print("Found diffs")
        logging.info("Found diffs:")
        for diff in diffs:
            logging.info(diff)
        logging.info("End diffs")
        print("Upload Diffs")
        upload_diffs(diffs)


def upload_diffs(diffs: list):
    total = len(diffs)
    progress_index = 0
    for repositories in diffs:
        for repo_name, assets in repositories.items():
            for asset in assets:
                download_asset(asset)
            progress(progress_index, total, status='Upload packages to the repository - ' + repo_name)
            url = TARGET_NEXUS_URL + "/service/rest/v1/components?repository=" + repo_name
            if REPO_FORMAT == "raw":
                upload_raw_assets(repo_name, url)
            elif REPO_FORMAT == "composer":
                upload_composer_assets(repo_name)
            elif REPO_FORMAT == "maven2":
                upload_maven(repo_name)
            elif REPO_FORMAT == "nuget" or REPO_FORMAT == "pypi" or REPO_FORMAT == "maven2":
                upload_assets(repo_name, url)
            progress_index += 1
    progress(progress_index, total, status='Upload packages to the repository - Done')
    return


def get_body_for_repo_hosted(name: str) -> dict:
    if REPO_FORMAT == "nuget" or REPO_FORMAT == "pypi":
        return {
            "name": name,
            "online": True,
            "storage": {
                "blobStoreName": "default",
                "strictContentTypeValidation": True,
                "writePolicy": "allow_once"
            }
        }
    elif REPO_FORMAT == "raw":
        return {
            "name": name,
            "online": True,
            "storage": {
                "blobStoreName": "default",
                "strictContentTypeValidation": True,
                "writePolicy": "allow_once"
            },
            "raw": {
                "contentDisposition": "ATTACHMENT"
            }
        }
    elif REPO_FORMAT == "maven2":
        return {
            "name": name,
            "online": True,
            "storage": {
                "blobStoreName": "default",
                "strictContentTypeValidation": True,
                "writePolicy": "allow_once"
            },
            "cleanup": {
                "policyNames": [
                    "string"
                ]
            },
            "component": {
                "proprietaryComponents": True,
            },
            "maven": {
                "versionPolicy": "MIXED",
                "layoutPolicy": "STRICT"
            }
        }
    else:
        return {}


def upload_raw_assets(repo_name: str, url: str) -> None:
    tree = os.walk(DOWNLOAD_DIR + "/" + repo_name)
    for tree_list in tree:
        if len(tree_list[2]) > 0:
            for file in tree_list[2]:
                with open(tree_list[0] + "/" + file, "rb") as asset:
                    asset_dir = tree_list[0].split(DOWNLOAD_DIR + "/" + repo_name)
                    if len(asset_dir[1]) == 0:
                        directory = "/"
                    else:
                        directory = asset_dir[1]
                    file_json = {REPO_FORMAT + ".asset1": asset}
                    data_json = {
                        "raw.directory": directory,
                        "raw.asset1.filename": file
                    }
                    response = requests.post(
                        url,
                        files=file_json,
                        data=data_json,
                        auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS)
                    )
                    if response.status_code > 400:
                        logging.error("err:" + tree_list[0] + "/" + file + ": " + response.text)


def upload_composer_assets(repo_name: str) -> None:
    tree = os.walk(DOWNLOAD_DIR + "/" + repo_name)
    for tree_list in tree:
        if len(tree_list[2]) > 0:
            for file in tree_list[2]:
                with open(tree_list[0] + "/" + file, "rb") as asset:
                    asset_dir = tree_list[0].split(DOWNLOAD_DIR + "/" + repo_name)[1]

                    url = TARGET_NEXUS_URL + "/repository/" + repo_name + "/packages/upload" + asset_dir
                    # Method PUT cause: composer plugin not supported api
                    response = requests.put(url, data=asset, auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS))
                    if response.status_code > 400:
                        logging.error("err:" + tree_list[0] + "/" + file + ": " + response.text)


def upload_assets(repo_name: str, url: str) -> None:
    tree = os.walk(DOWNLOAD_DIR + "/" + repo_name)
    for tree_list in tree:
        if len(tree_list[2]) > 0:
            for file in tree_list[2]:
                with open(tree_list[0] + "/" + file, "rb") as asset:
                    file = {REPO_FORMAT + ".asset": asset}
                    response = requests.post(url, files=file, auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS))
                    if response.status_code > 400:
                        logging.error("err:" + tree_list[0] + "/" + file + ": " + response.text)


# HTTP PUT of a file into /content/repositories/<repo-id>/<path-of-file>.
def upload_maven(repo_name: str):
    tree = os.walk(DOWNLOAD_DIR + "/" + repo_name)
    for tree_list in tree:
        if len(tree_list[2]) > 0:
            for file in tree_list[2]:
                with open(tree_list[0] + "/" + file, "rb") as file_data:
                    asset_dir = tree_list[0].split(DOWNLOAD_DIR + "/" + repo_name)[1]

                    url = TARGET_NEXUS_URL + "/repository/" + repo_name + asset_dir + "/" + file
                    response = requests.put(url, data=file_data, auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS))
                    if response.status_code > 400:
                        logging.error("err:" + tree_list[0] + "/" + file + ": " + response.text)
