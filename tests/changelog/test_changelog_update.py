import unittest
from pontos import changelog


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
        updated, release_notes = changelog.update(test_md, '1.2.3')
        self.assertIs('', updated)
        self.assertIs('', release_notes)

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
        updated, release_notes = changelog.update(test_md, '1.2.3')

        self.assertEqual(released_md.strip(), updated.strip())
        self.assertEqual(released.strip(), release_notes.strip())
