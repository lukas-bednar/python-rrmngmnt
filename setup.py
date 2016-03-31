import os
from setuptools import setup


os.environ['SKIP_GENERATE_AUTHORS'] = '1'


if __name__ == "__main__":
    setup(
        setup_requires=['pbr'],
        pbr=True,
    )
