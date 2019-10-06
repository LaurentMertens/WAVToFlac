from setuptools import setup

setup(
    python_requires='>=3.6',
    name='wavtoflac',
    version='1.0',
    packages=['wavtoflac'],
    url='',
    license='MIT',
    author='Laurent Mertens',
    author_email='laurent.mertens@outlook.com',
    description='WAV To Flac',
    install_requires=['mutagen',
                      'pydub',
                      'termcolor']
)
