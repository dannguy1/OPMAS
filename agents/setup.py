from setuptools import setup, find_packages

setup(
    name="opmas-agents",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "nats-py",
        "structlog",
        "python-dotenv",
        "psutil",
        "pytest-mock",
    ],
    python_requires=">=3.8",
) 