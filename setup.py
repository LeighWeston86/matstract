from setuptools import setup

setup(
    name='matstract',
    packages = ['matstract'],
    version='0.0',
    author='Matstract Development Team',
    author_email='jdagdelen@berkeley.edu',
    description='Materials extraction from scientific abstracts.',
    url='https://github.com/materialsintelligence/matstract',
    download_url = 'https://github.com/materialsintelligence/matstract/archive/0.0.tar.gz',
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
