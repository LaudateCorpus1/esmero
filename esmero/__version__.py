"""esmero version

version_info conforms to PEP 386

(major, minor, micro, alpha/beta/rc/final, #)
(1, 1, 2, 'alpha', 0) => "1.1.2.dev"
(1, 2, 0, 'beta', 2) => "1.2b2"

"""

VERSION_INFO = (0, 0, 0, 'alpha', 0)


def get_version(version_info):
    """Return a PEP-386 compliant version number from version_info."""
    assert len(version_info) == 5
    assert version_info[3] in ('alpha', 'beta', 'rc', 'final')

    parts = 2 if version_info[2] == 0 else 3
    main = '.'.join([str(part) for part in version_info[:parts]])

    sub = ''
    if version_info[3] == 'alpha' and version_info[4] == 0:
        sub = '.dev'
    elif version_info[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version_info[3]] + str(version_info[4])

    return str(main + sub)

VERSION = get_version(VERSION_INFO)
