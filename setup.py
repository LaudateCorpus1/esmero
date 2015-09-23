"""esmero setup script"""

import imp
import os.path as pt
from setuptools import setup


def get_version():
    "Get version & version_info without importing esmero.__init__ "
    path = pt.join(pt.dirname(__file__), 'esmero', '__version__.py')
    mod = imp.load_source('esmero_version', path)
    return mod.VERSION, mod.VERSION_INFO

VERSION, VERSION_INFO = get_version()

DESCRIPTION = "Website builder."
LONG_DESCRIPTION = "Esmero is a website builder relying in lexor."

DEV_STATUS_MAP = {
    'alpha': '3 - Alpha',
    'beta': '4 - Beta',
    'rc': '4 - Beta',
    'final': '5 - Production/Stable'
}
if VERSION_INFO[3] == 'alpha' and VERSION_INFO[4] == 0:
    DEVSTATUS = '2 - Pre-Alpha'
else:
    DEVSTATUS = DEV_STATUS_MAP[VERSION_INFO[3]]

setup(name='esmero',
      version=VERSION,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      keywords='esmero lexor html',
      author='Manuel Lopez',
      author_email='jmlopez.rod@gmail.com',
      url='http://jmlopez-rod.github.io/esmero',
      license='BSD License',
      packages=[
          'esmero',
          'esmero.command',
          ],
      scripts=['bin/esmero'],
      install_requires=[
          'lexor',
          'nose>=1.3',
          ],
      package_data={
          #'esmero.core': ['*.txt'],
          },
      include_package_data=True,
      classifiers=[
          'Development Status :: %s' % DEVSTATUS,
          'License :: OSI Approved :: BSD License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Topic :: Documentation',
          'Topic :: Communications :: Email',
          'Topic :: Text Processing',
          'Topic :: Text Processing :: Linguistic',
          'Topic :: Text Processing :: Markup',
          ],
      )
