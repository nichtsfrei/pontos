import argparse
import sys
import subprocess
import os
import json
from pathlib import Path


import requests
from pontos import version
from pontos import changelog

# from pontos import changelog

# 1. update version
# 2. update markdown
# 3. create commit
# 3. create tag
# 4. push tag
# 5. create release:
# https://docs.github.com/en/rest/reference/repos#create-a-release
# 6. upload assets:
# https://docs.github.com/en/rest/reference/repos#upload-a-release-asset


def build_release_dict(
    release_version: str,
    release_changelog: str,
    name: str = '',
    target_commitish: str = '',  # needed when tag is not there yet
    draft: bool = False,
    prerelease: bool = False,
):
    """
    builds the dict for release post on github, see:
    https://docs.github.com/en/rest/reference/repos#create-a-release
    for more details.
    """
    tag_name = (
        release_version
        if release_version.startswith('v')
        else "v" + release_version
    )
    return {
        'tag_name': tag_name,
        'target_commitish': target_commitish,
        'name': name,
        'body': release_changelog,
        'draft': draft,
        'prerelease': prerelease,
    }


def initialize_default_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Release handling utility.', prog='pontos-release',
    )
    parser.add_argument(
        '--release-version',
        help='Will release changelog as version. Must be PEP 440 compliant',
    )
    parser.add_argument(
        '--next-release-version',
        help='Sets the next PEP 440 compliant version in project definition.',
    )
    parser.add_argument(
        '--project', help='The github project',
    )
    parser.add_argument(
        '--space', default='greenbone', help='user/team name in github',
    )

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        help='additional help',
        dest='command',
    )

    subparsers.add_parser('release')
    subparsers.add_parser('dry-run')
    return parser


def run(args=None):
    parser = initialize_default_parser()
    commandline_arguments = parser.parse_args(args)
    needed_attr = [
        'command',
        'release_version',
        'next_release_version',
        'project',
    ]
    for attr in needed_attr:
        if not getattr(commandline_arguments, attr, None):
            parser.print_usage()
            return None
    token = os.environ['GITHUB_TOKEN']
    if token == '':
        raise ValueError("github token not set in environmnet")
    user = os.environ['GITHUB_USER']
    if user == '':
        raise ValueError("github user not set in environmnet")
    return (
        commandline_arguments.command,
        commandline_arguments.release_version,
        commandline_arguments.next_release_version,
        commandline_arguments.project,
        commandline_arguments.space,
        user,
        token,
    )


def execute(
    command, release_version, next_release_version, project, space, user, token
):
    if command == 'release':
        return release(
            release_version, next_release_version, project, space, user, token
        )


def release(
    release_version: str,
    nextversion: str,
    project: str,
    space: str,
    username: str,
    token: str,
    dry_run: bool = False,
    git_tag_prefix="v",
):
    print("in release")
    executed, filename = version.main(
        False, args=["--quiet", "update", nextversion]
    )
    if not executed:
        if filename == "":
            print("No project definition found.")
        else:
            print("Unable to update version {} in {}", nextversion, filename)
        sys.exit(2)
    print("updated version {} to {}".format(filename, nextversion))
    change_log_path = Path.cwd() / 'CHANGELOG.md'
    updated, changelog_text = changelog.update(
        change_log_path.read_text(),
        release_version,
        project,
        git_tag_prefix=git_tag_prefix,
        git_space=space,
    )
    change_log_path.write_text(updated)
    print("updated CHANGELOG.md")
    if not dry_run:
        git = GithubCommand(
            token, username, project, space=space, tag_prefix=git_tag_prefix
        )
        return git.commit_changes(filename, release_version, changelog_text)
    return True


class GithubCommand:
    space = None
    project = None
    token = None
    user = None
    tag_prefix = None

    def __init__(
        self,
        token: str,
        user: str,
        project: str,
        space: str = 'greenbone',
        tag_prefix: str = 'v',
    ):
        self.token = token
        self.username = user
        self.project = project
        self.space = space
        self.tag_prefix = tag_prefix

    def commit_changes(
        self, project_filename: str, release_version: str, changelog_text: str,
    ):
        """
        commit_changes adds:
        - filename
        - CHANGELOG.md
        commits those changes, creates a tag based on:
        - release_version
        - tag_prefix
        pushes to changes and than creates a release for feshly created tag.
        """
        subprocess.run(
            "git add {}".format(project_filename), shell=True, check=True
        )
        subprocess.run("git add CHANGELOG.md", shell=True, check=True)
        commit_msg = 'automatic release to {}'.format(release_version)
        subprocess.run(
            "git commit -S -m '{}'".format(commit_msg), shell=True, check=True,
        )
        git_version = "{}{}".format(self.tag_prefix, release_version)
        subprocess.run(
            "git tag -s {} -m '{}'".format(git_version, commit_msg),
            shell=True,
            check=True,
        )
        subprocess.run("git push --follow-tags", shell=True, check=True)
        release_info = build_release_dict(git_version, changelog_text)
        headers = {'Accept': 'application/vnd.github.v3+json'}
        base_url = "https://api.github.com/repos/{}/{}/releases".format(
            self.space, self.project
        )
        auth = (self.username, self.token)
        response = requests.post(
            base_url, headers=headers, auth=auth, json=release_info
        )
        if response.status_code != 201:
            print("Wrong reponse status code: {}".format(response.status_code))
            print(json.dumps(response.text, indent=4, sort_keys=True))
            return False
        return True


def main():
    values = run()
    if not values:
        sys.exit(1)
    execute(*values)


if __name__ == '__main__':
    main()
