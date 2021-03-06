import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="serverless_machine_learning_api",
    version="0.0.1",

    description="Serverless machine learning API using PyTorch running in AWS Lambda",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="author",

    package_dir={"": "serverless_machine_learning_api"},
    packages=setuptools.find_packages(where="serverless_machine_learning_api"),

    install_requires=[
        "aws-cdk.core==1.61.1",
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
