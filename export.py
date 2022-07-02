from common import *

# Скрипт загружает пакеты в nexus - TARGET_NEXUS_URL
# Из папки DOWNLOAD_DIR (репозитории создаются по названию входящих директорий)


def main():
    repositories = get_repositories_from_download_dir()
    progress_index = 0
    total = len(repositories)
    for name in repositories:
        progress(progress_index, total, status='Creating repositories - ' + name)
        create_repo(name)
        progress_index += 1
    progress(progress_index, total, status='Creating repositories - Done')

    progress_index = 0
    for repo_name in repositories:
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


if __name__ == '__main__':
    try:
        if FULL == "true":
            main()
            #search_diff()
        else:
            search_diff()
    except Exception as e:
        logging.error('Failed.', exc_info=e)
