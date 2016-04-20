#!/usr/bin/env python

from datetime import datetime
import os
from setuptools import setup
import subprocess


def version():
    from_file, from_git = None, None
    receipt = 'ahab/version/VERSION'
    default = datetime.utcnow().strftime('%Y%m%d') + '+unversioned'
    if os.path.exists('.git'):
        try:
            txt = subprocess.check_output(['git', 'describe', '--tags'])
            from_git = txt.strip().replace('-', '.', 1).replace('-g', '+', 1)
        except subprocess.CalledProcessError:
            pass
    if os.path.exists(receipt):
        with open(receipt) as h:
            txt = h.read().strip()
            if txt != '':
                from_file = txt
    version = from_git or from_file or default
    with open(receipt, 'w+') as h:
        h.write(version + '\n')
    return version


setup(name='ahab',
      maintainer='Instacart',
      maintainer_email='open-source@instacart.com',
      url='https://github.com/instacart/ahab',
      version=version(),
      install_requires=['argh',
                        'docker-py',
                        'magiclog'],
      setup_requires=['setuptools'],
      tests_require=['flake8'],
      description='Ahab: on which to hang your Docker hooks',
      packages=['ahab',
                'ahab.version'],
      package_data={'ahab.version': ['VERSION']},
      entry_points={'console_scripts': ['ahab = ahab.__main__:main']},
      classifiers=['Environment :: Console',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: ISC License (ISCL)',
                   'Operating System :: Unix',
                   'Operating System :: POSIX',
                   'Programming Language :: Python',
                   'Topic :: System',
                   'Topic :: System :: Systems Administration',
                   'Topic :: Software Development',
                   'Development Status :: 4 - Beta'])
