from setuptools import setup

setup(name="gimmeashell",
      description="A nice wrapper for exploited command execution or reverse shells.",
      url="https://github.com/LosFuzzys/gimmeashell",
      version="0.0.1",
      license='MIT',
      install_requires=[
          "requests",
          "pwntools",
          ],
      classifiers = [
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: MIT License',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python :: 2.7',
          'Topic :: Security',
          'Topic :: System :: System Shells',
          ]
)
