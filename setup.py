from setuptools import setup, find_packages


setup(
    name="time-lapse-pi",
    version="1.0",
    description="Time-lapse capture for rPi",
    long_description="Time-lapse capture for rPi",
    author="Dustin J. Mitchell",
    author_email="dustin@v.igoro.us",
    license="BSD",
    packages=find_packages(),
    install_requires=[
        'boto3',
        'pyyaml',
        'pillow',
    ],
    include_package_data=True,
    zip_safe=False,
    scripts=[],
    entry_points={
        'console_scripts': [
            "time-lapse-pi = timelapsepi.main:main",
        ],
    },

    classifiers=[
        'Programming Language :: Python',
    ],
)
