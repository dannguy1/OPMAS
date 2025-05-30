from setuptools import setup, find_packages

setup(
    name="opmas_agents",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "nats-py>=2.0.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "pyyaml>=6.0.0",
        "aiohttp>=3.8.0",
        "asyncio>=3.4.3",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "pylint>=2.17.0",
        ]
    },
    python_requires=">=3.9",
    author="OPMAS Team",
    author_email="team@opmas.org",
    description="OPMAS Agent System",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/opmas/agents",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 