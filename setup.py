from setuptools import setup

setup(
    name='fitbit-cli',
    version='0.1',
    py_modules=['fitbit_cli'],
    install_requires=[
        'Click',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        fitbit=fitbit_cli:fitbit
    ''',
)
