from setuptools import setup, find_packages

requires = [
    'argparse',
    'requests',
    'pytz',
    'websocket_client',
    'bs4',
]

setup(
    name='emberpulse',
    version='0.0.1',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'emberpulse-stats = emberpulse.stats:main'
        ]
    },
)