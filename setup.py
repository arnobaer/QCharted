from setuptools import setup

setup(
    name='QCharted',
    version='1.0.0',
    author="Bernhard Arnold",
    author_email="bernhard.arnold@oeaw.ac.at",
    py_modules=['QCharted'],
    install_requires=[
        'numpy>=1.17',
        'PyQt5>=5.13',
        'PyQtChart>=5.13',
    ],
    test_suite='tests',
    license="GPLv3",
)
