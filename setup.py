from setuptools import setup, find_packages

setup(
    name="user-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg2-binary",
        "mangum",
        "faker",
        "boto3",
        "aws-lambda-powertools",
        "aws-xray-sdk",
        "python-json-logger",
    ],
    python_requires=">=3.11",
) 
