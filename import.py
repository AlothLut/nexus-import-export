from common import *


# Сохраняет пакеты из nexus - SOURCE_NEXUS_URL
# В папку DOWNLOAD_DIR
# Пакеты выбираются по REPO_TYPE и REPO_FORMAT


def main():
    try:
        create_download_dir()
        repositories = get_repositories_from_nexus(SOURCE_NEXUS_URL, SOURCE_NEXUS_USER, SOURCE_NEXUS_PASS)
        progress_index = 0
        total = len(repositories)
        for repo in repositories:
            progress(progress_index, total, status='Downloading packages from the repository - ' + repo)
            assets = get_all_assets(SOURCE_NEXUS_URL, repo, SOURCE_NEXUS_USER, SOURCE_NEXUS_PASS)

            for asset in assets:
                download_asset(asset)
            progress_index += 1
        progress(progress_index, total, status='Downloading packages from the repository - Done')
    except Exception as e:
        logging.error('Failed.', exc_info=e)


if __name__ == '__main__':
    main()
