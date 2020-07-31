from pathlib import Path
import pontos

# from pontos import changelog

# 1. update version
# 2. update markdown
# 3. create tag
# 4. push tag
# 5. create release:
# https://docs.github.com/en/rest/reference/repos#create-a-release
# 6. upload assets:
# https://docs.github.com/en/rest/reference/repos#upload-a-release-asset


def build_release_dict(
    version: str,
    changelog: str,
    name: str = None,
    target_commitish: str = None,  # needed when tag is not there yet
    draft: bool = False,
    prerelease: bool = False,
):
    """
    builds the dict for release post on github, see:
    https://docs.github.com/en/rest/reference/repos#create-a-release
    for more details.
    """
    tag_name = version if version.startswith('v') else "v" + version
    return {
        'tag_name': tag_name,
        'target_commitish': target_commitish,
        'name': name,
        'body': changelog,
        'draft': draft,
        'prerelease': prerelease,
    }


def main():
    print("going to upgrade")
    change_log_path = Path.cwd() / 'CHANGELOG.md'
    pontos.changelog.update(change_log_path.read_text(), '0.0.2')
    pontos.version.main(args=["update"])
