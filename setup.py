import os

from setuptools import setup, find_packages


package_name = 'pangaea'
version_file = 'version.py'

with open('requirements.txt') as f:
    required = f.read().splitlines()

def get_version(package_name=package_name, filename=version_file):
    version_path = os.path.join(package_name, version_file)
    return open(version_path).read().split('=')[-1].strip(' \'"\n')


setup(
    name='pangaea',
    description='Parse research for gene interactions',
    version=get_version(),
    url='https://github.com/ss-lab-cancerunit/pangaea',
    packages=find_packages(),
    install_requires=required,
    include_package_data=True,
    entry_points={
        'console_scripts': ['pangaea=pangaea.__main__:main'],
    }
)
