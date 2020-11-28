from setuptools import setup


setup(
    name='grow-ext-static-server',
    version='1.1.1',
    license='MIT',
    author='Grow.dev Authors',
    author_email='hello@grow.io',
    package_data={
        'grow_static_server': ['*.yaml'],
    },
    packages=[
        'grow_static_server',
    ],
)
