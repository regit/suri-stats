#!/usr/bin/env python
from setuptools import setup

setup(name='suri-stats',
      version='0.2',
      description='Tools to output graphic and stats using Suricata stats.log file',
      author='Eric Leblond',
      author_email='eric@regit.org',
      url='http://home.regit.org/software/suri-stats/',
      scripts=['suri-stats'],
      packages=['suristats'],
      package_dir={'suristats':'src'},
      provides=['suristats'],
      requires=['pylab', 'numpy', 'ipython'],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development :: Quality Assurance'
          ],
      )
