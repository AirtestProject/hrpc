# coding=utf-8

from setuptools import setup, find_packages


def parse_requirements(filename='requirements.txt'):
    """ load requirements from a pip requirements file. (replacing from pip.req import parse_requirements)"""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


setup(
    name='hrpc',
    version='1.0.8',
    keywords="hrpc rpc",
    description='A common interface based RPC framework',
    packages=find_packages(),
    include_package_data=True,
    install_requires=parse_requirements(),
    license='Apache License 2.0',
    url='https://github.com/AirtestProject/hrpc',
)
