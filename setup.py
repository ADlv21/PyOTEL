"""
Setup script for simple_logger package.
"""

from setuptools import setup, find_packages

setup(
    name="pyotel",
    version="0.1.0",
    description="A simple request/response logger with trace ID propagation for FastAPI",
    author="ADv8",
    author_email="adwaitg02@gmail.com",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "starlette>=0.14.2",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)