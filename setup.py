from pathlib import Path
from setuptools import find_packages, setup


requirements = [
    'opencv-python',
    'av',
    'ffmpeg',
    'websockets',
]


extras_require = {
    'test': ['pytest'],
}


setup(
    name='psivideo',
    author='psivideo development team',
    install_requires=requirements,
    extras_require=extras_require,
    packages=find_packages(),
    include_package_data=True,
    license='LICENSE.txt',
    description='Audio tools supporting psiexperiment',
    entry_points={
        'console_scripts': [
            'psivideo=psivideo.main:main',
        ],
    },
    #version=version,
)
