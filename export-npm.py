from common import *


# Скрипт загружает npm пакеты в nexus - TARGET_NEXUS_URL
# Из папки DOWNLOAD_DIR
# repo захардкожены из-за условий задачи


def main(repeat=False, diff_assets=[]):
    repo_our = "npm-action"
    repo_freeze = "npm-freeze"
    our_projects = ["@arm-seller/action-ui-kit", "@action/eslint-config", "@arm-seller/action-ui-kit-min",
                    "@action/api-services-example", "@action/application", "@action/assets-loader",
                    "@action/auth-button",
                    "@action/auth-button-api", "@action/component-button", "@action/component-icon", "@action/config",
                    "@action/dev-tools", "@action/dev-tools-new", "@action/evercookie", "@school/heatmap-frontend",
                    "@action/jest-config", "@action/logger", "@arm-seller/logger", "@action/manifest",
                    "@action/marketing-actions",
                    "@action/metrics", "@action/metrics-sender", "@action/middlewares", "@action/network",
                    "@product-platform/react-hooks", "@action/react-renderer", "@product-platform/react-virtual",
                    "@action/renderer",
                    "@action/server", "@action/test-ci-library", "@action/test-ci-library-new",
                    "@action/test-ci-library-new3",
                    "@action/tslint-config", "@school/ui-kit", "@product-platform/ui-kit-react",
                    "@action/ui-module-example",
                    "@product-platform/utils", "@action/vue-renderer", "@action/webarm-components",
                    "@action/webarm-treeselect",
                    "@action/widget", "@action/client", "@product-platform/test-helpers",
                    "@product-platform/test-utils",
                    "@arm-seller/api-tools", "@arm-seller/api-services-template", "@arm-seller/ui-module-template",
                    "@action/eslint-base-config", "@action/eslint-react-config", "@action/eslint-vue-config",
                    "@action/eslint-config-base", "@action/eslint-config-react", "@action/eslint-config-vue",
                    "@action/log"
                    ]
    tree = os.walk(DOWNLOAD_DIR)
    for tree_list in tree:
        if len(tree_list[2]) > 0:
            for file_name in tree_list[2]:
                asset_dir = tree_list[0].split(DOWNLOAD_DIR + "/")
                if asset_dir[1] in our_projects:
                    url = TARGET_NEXUS_URL + "/service/rest/v1/components?repository=" + repo_our
                else:
                    url = TARGET_NEXUS_URL + "/service/rest/v1/components?repository=" + repo_freeze

                if not repeat:
                    if file_name != 'package.json':
                        print('upload ' + file_name)
                        with open(tree_list[0] + "/" + file_name, "rb") as asset:
                            file = {REPO_FORMAT + ".asset": asset}
                            response = requests.post(url, files=file, auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS))
                            if response.status_code > 400:
                                logging.error("err:" + tree_list[0] + "/" + file_name + ": " + response.text)
                else:
                    if file_name != 'package.json' and file_name in diff_assets:
                        print('#################upload diffs########################3')
                        print('upload ' + file_name)
                        with open(tree_list[0] + "/" + file_name, "rb") as asset:
                            file = {REPO_FORMAT + ".asset": asset}
                            response = requests.post(url, files=file, auth=(TARGET_NEXUS_USER, TARGET_NEXUS_PASS))
                            if response.status_code > 400:
                                logging.error("err:" + tree_list[0] + "/" + file_name + ": " + response.text)

    progress(1, 1, status='Done')


def check_diff():
    repose = ["npm-hosted-action", "npm-freeze"]
    repose = ["npm-freeze"]
    nexus_assets = []
    for repo in repose:
        target_assets = get_all_assets(TARGET_NEXUS_URL, repo, TARGET_NEXUS_USER, TARGET_NEXUS_PASS)
        assets = get_assets_name(target_assets)
        nexus_assets.extend(assets)

    tree = os.walk(DOWNLOAD_DIR)
    local_assets = []
    for tree_list in tree:
        if len(tree_list[2]) > 0:
            for file_name in tree_list[2]:
                if file_name != 'package.json':
                    local_assets.append(file_name)

    for name in local_assets.copy():
        print('check ' + name)
        if name in nexus_assets:
            local_assets.remove(name)

    if len(local_assets) > 0:
        print("Found diffs")
        logging.info("Found diffs:")
        for diff in local_assets:
            logging.info(diff)
        logging.info("End diffs")
        print("upload diffs")
        main(True, local_assets)


def get_assets_name(assets):
    result = []
    for asset in assets:
        name = asset['path'].split("/")[-1]
        result.append(name)
    return result


if __name__ == '__main__':
    try:
        #main()
        check_diff()
    except Exception as e:
        logging.error('Failed.', exc_info=e)
