from setuptools import setup, find_packages

setup(
    name="game-forum",
    version="1.0.0",
    py_modules=['app'],
    include_package_data=True,
    install_requires=[
        'Flask>=2.0.1',
        'Flask-SQLAlchemy>=2.5.1',
        'Flask-Login>=0.5.0',
        'Flask-Migrate>=3.1.0',
        'Werkzeug>=2.0.1',
    ],
    entry_points={
        'console_scripts':[
            'game-forum=app:main'
        ]
    },
    python_requires='>=3.8',
)