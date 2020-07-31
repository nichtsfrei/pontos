import unittest
from pontos.changelog import Changelog


class ChangelogUpdateTestCase(unittest.TestCase):
    def test_markdown_empty_updated_and_changelog_on_no_unreleased(self):
        test_md = """
# Changelog
something, somehing
- unreleased
- not unreleased
## 1.0.0
### added
- cool stuff 1
- cool stuff 2
"""
        original, updated, changelog = Changelog(test_md).update('1.2.3')
        self.assertIs(original, test_md)
        self.assertIs('', updated)
        self.assertIs('', changelog)

    def test_update_markdown_return_changelog(self):
        released = """
## [1.2.3] - 2020-07-31
### fixed
so much
### added
so little
### changed
I don't recognize it anymore
### security
[1.2.3]: https://github.com/greenbone/pontos/compare/v1.0.0...v1.2.3"""

        unreleased = """
## [Unreleased]
### fixed
so much
### added
so little
### changed
I don't recognize it anymore
### security
[Unreleased]: https://github.com/greenbone/pontos/compare/v1.0.0...master"""
        test_md_template = """# Changelog
something, somehing
- unreleased
- not unreleased
{}
## 1.0.0
### added
- cool stuff 1
- cool stuff 2"""
        test_md = test_md_template.format(unreleased)
        released_md = test_md_template.format(released)
        original, updated, changelog = Changelog(test_md).update('1.2.3')

        self.assertIs(original, test_md)
        self.assertEqual(released_md.strip(), updated.strip())
        self.assertEqual(released.strip(), changelog.strip())
