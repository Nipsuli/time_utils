from setuptools import setup


with open("README.md", "r") as f:
    readme = f.read()


setup(
    name="time_utils",
    version="0.2.0",
    description="Collection of time related utils",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/Nipsuli/time_utils",
    author="Niko Ahonen",
    author_email="n.p.ahonen@gmail.com",
    license="MIT",
    packages=["time_utils"],
    install_requires=[
        "python_version>='3.6'",
        "pytz>=2019.1",
        "tzlocal>=1.5.1",
        "python-dateutil>=2.8.0"
    ],
    python_requires=">=3.6",
    keywords="time utils timezone datetime",
    setup_requires=["pytest-runner"],
    tests_require=[
        "freezegun>=0.3.11"
        "pytest>=4.0.2"
        "pytest-cov>=2.6.0"
    ]
)
