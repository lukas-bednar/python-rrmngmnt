import os
from setuptools import setup

def read(fname):
    return open(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), fname,
            )
        )
    ).read()

setup(
    name="rrmngmnt",
    version="0.1",
    author="Lukas Bednar",
    author_email="lukyn17@gmail.com",
    description="Tool to manage remote systems and services.",
    license="GPL2",
    keywords="remote resources services",
    url="https://github.com/lukas-bednar/python-rrmngmnt",
    platforms=['linux'],
    packages=['rrmngmnt'],
    long_description=read('README.md'),
    install_requires=['paramiko', 'netaddr'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License 2 (GPL2)",
        "Operating System :: POSIX",
        "Programming Language :: Python",
    ],
)
