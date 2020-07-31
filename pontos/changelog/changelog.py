# Copyright (C) 2020 Greenbone Networks GmbH
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import re
from typing import Tuple, Generator, Optional
from datetime import date


class ChangelogError(Exception):
    """
    Some error has occurred during changelog handling
    """


class Changelog:

    __cmake_scanner = None
    _markdown = None

    def __init__(self, markdown: str, git_tag_prefix='v'):
        self._markdown = markdown
        self.__cmake_scanner = self.__build_scanner()
        self._git_tag_prefix = git_tag_prefix

    __unreleased_matcher = re.compile("unreleased", re.IGNORECASE)
    __master_matcher = re.compile("master")

    def update(
        self, new_version: str, containing_version: str = None
    ) -> Tuple[str, str, str]:
        """
        update tokenizes CHANGELOG.md and if a version is given it changes
        unreleased headline and link to given version.

        returns original markdown, updated markdown and change log for further
        processing.
        """
        tokens = self._tokenize()
        hc = 0
        changelog = ""
        updated_markdown = ""
        may_changelog_relevant = True
        for tt, heading_count, tc in tokens:
            if tt == 'unreleased':
                if (
                    containing_version and containing_version in tc
                ) or not containing_version:
                    hc = heading_count
                    if new_version:
                        tc = self.__unreleased_matcher.sub(new_version, tc)
                        tc += " - {}".format(date.today().isoformat())
            elif heading_count > 0 and hc > 0 and heading_count <= hc:
                may_changelog_relevant = False
            if tt == 'unreleased_link' and new_version:
                tc = self.__unreleased_matcher.sub(new_version, tc)
                tc = self.__master_matcher.sub(
                    "{}{}".format(self._git_tag_prefix, new_version), tc
                )

            updated_markdown += tc
            if may_changelog_relevant:
                append_word = hc > 0
                if append_word:
                    changelog += tc

        return (
            self._markdown,
            updated_markdown if changelog else "",
            changelog,
        )

    def changelog(
        self, new_version: str = None, containing_version: str = None
    ) -> Optional[str]:
        _, _, result = self.update(new_version, containing_version)
        return result if result else None

    def __build_scanner(self):
        def token_handler(key: str):
            """
            generates a lambda for the regex scanner with a given key.

            This lambda will return a tuple: key, count # of token and token.

            The count is used to identify the level of heading on a special
            ended which can be used to identify when this section ended.
            """
            return lambda _, token: (key, token.count('#'), token)

        return re.Scanner(
            [
                (r'#{1,} Added', token_handler('added')),
                (r'#{1,} Changed', token_handler("changed")),
                (r'#{1,} Deprecated', token_handler("deprecated")),
                (r'#{1,} Removed', token_handler("removed")),
                (r'#{1,} Fixed', token_handler("fixed")),
                (r'#{1,} Security', token_handler("security")),
                (r'#{1,}.*(?=[Uu]nreleased).*', token_handler("unreleased")),
                (r'\[[Uu]nreleased\].*', token_handler("unreleased_link"),),
                (r'#{1,} .*', token_handler("heading")),
                (r'\n', token_handler("newline")),
                (r'..*', token_handler("any")),
            ]
        )

    def _tokenize(
        self,
    ) -> Generator[
        Tuple[int, str, int, str],
        Tuple[int, str, int, str],
        Tuple[int, str, int, str],
    ]:
        toks, remainder = self.__cmake_scanner.scan(self._markdown)
        if remainder != '':
            print('WARNING: unrecognized tokens: {}'.format(remainder))
        return toks
