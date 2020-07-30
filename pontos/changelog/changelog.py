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
from typing import Tuple, Generator
from pathlib import Path


class ChangelogError(Exception):
    """
    Some error has occurred during changelog handling
    """


class ChangelogParser:

    __cmake_scanner = None
    _markdown = None

    def __init__(self, markdown: str):
        self._markdown = markdown
        self.__cmake_scanner = self.__build_scanner()

    __unreleased_matcher = re.compile("unreleased", re.IGNORECASE)

    def find_unreleased(
        self, containing_version: str = None
    ) -> Tuple[int, int, str]:
        tokens = self._tokenize()
        start_ln = 0
        hc = 0
        result = []
        for ln, tt, heading_count, tc in tokens:
            if tt == 'unreleased':
                if containing_version and tc.contains(containing_version):
                    start_ln = ln
                    hc = heading_count
                elif not containing_version:
                    start_ln = ln
                    hc = heading_count
            elif heading_count > 0 and hc > 0 and heading_count <= hc:
                return (start_ln, ln, "\n".join(result))
            append_word = hc > 0
            if append_word:
                result.append(tc)

        if start_ln > 0:
            return (start_ln, len(tokens) - 1, "\n".join(result))

        raise ChangelogError("No unreleased information found.")

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
        line_num = 0
        for tok_type, heading_count, tok_contents in toks:
            line_num += tok_contents.count('\n')
            yield line_num, tok_type, heading_count, tok_contents.strip()


if __name__ == "__main__":
    PATH = Path.cwd() / "CHANGELOG.md"
    PARSER = ChangelogParser(PATH.read_text())
    print(PARSER.find_unreleased()[2])
    print(PARSER.find_unreleased()[0])
    print(PARSER.find_unreleased()[1])
