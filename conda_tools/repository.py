
PACKAGE_FIELDS = (
    'build', 'build_number', 'date', 'date', 'depends', 'requires',
    'license', 'license_family', 'md5', 'size', 'version', 'name'
)

class RepoPackage(object):
    __slots__ = ('filename',) + PACKAGE_FIELDS    
    def __init__(self, filename, info):
        self.filename = filename

        for field in PACKAGE_FIELDS:
            setattr(self, field, info.get(field))

    def __hash__(self):
        return hash(self.md5)

    def __repr__(self):
        return 'RepoPackage({})'.format(self.filename)

    def __str__(self):
        return '{} {} {}'.format(self.name, self.version, self.build)


def repo_packages(d):
    return set(RepoPackage(*info) for info in d.items())

class Repository(object):
    def __init__(self, url, data):
        self.url = url
        self.arch = data['info']['arch']
        self.platform = data['info']['platform']
        self.packages = repo_packages(data['packages'])

    def __repr__(self):
        return 'Repository({})'.format(self.url)

    def __eq__(self, other):
        try:
            return (self.url == other.url) and (self.packages == other.packages)
        except:
            return False