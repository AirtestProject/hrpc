from distutils.core import setup
from pip.req import parse_requirements


# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements('requirements.txt', session=False)

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]

setup(
    name='hrpc',
    version='0.0.1',
    py_modules=['hrpc'],
    packages=['hrpc'],
    install_requires=reqs,
)
