import os
import setuptools
import sys

if sys.version_info[0] < 3:
    sys.exit("Rupee requires Python 3.")

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    author='Tommy MacWilliam',
    author_email='tmacwilliam@cs.harvard.edu',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3 :: Only',
    ],
    description='A fully-featured cache for Python applications.',
    install_requires=[
    ],
    license='MIT',
    long_description=long_description,
    keywords='cache caching redis memcache memcached',
    name='rupee',
    packages=setuptools.find_packages(),
    url='https://github.com/tmacwill/rupee',
    version='0.0.1',
)
