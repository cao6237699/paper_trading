from setuptools import setup

setup(
    name='paper_trading',
    version='1.1.0',
    description='creat your own paper trading server',
    long_description='',
    author=['Michael'],
    author_email='cao6237699@126.com',
    url='https://github.com/cao6237699/paper_trading.git',
    packages=[
        'paper_trading'
    ],
    py_modules=['run'],
    include_package_data=True,
    platforms='any',
    install_requires=[
        'pytdx',
        'requests',
        'flask',
        'mongodb',
        'tushare'
    ],
    license='MIT License',
    zip_safe=False,
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 3.7.3',
        'Programming Language :: Python :: Implementation :: CPython'
    ]
)
