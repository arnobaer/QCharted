from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='QCharted',
    version='1.1.1',
    author="Bernhard Arnold",
    author_email="bernhard.arnold@oeaw.ac.at",
    url = "https://github.com/arnobaer/QCharted",
    description="Plotting large data series using PyQtChart.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['QCharted'],
    install_requires=[
        'numpy>=1.17',
        'PyQt5>=5.12',
        'PyQtChart>=5.12',
    ],
    test_suite='tests',
    license="GPLv3",
)
