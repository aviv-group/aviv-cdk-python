import setuptools
import aviv_cdk

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aviv-cdk", # Replace with your own username
    version=aviv_cdk.__version__,
    author="Jules Clement",
    author_email="jules.clement@aviv-group.com",
    description="Aviv CDK Python library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aviv-group/aviv-cdk-python",
    packages=setuptools.find_packages(
        include=['aviv_cdk']
    ),
    package_data={
        "lambdas": [
            "cfn_resources/requirements.txt",
            "iam_idp/saml.py"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'aviv-aws=bin.aws_local:cli',
            'aviv-cdk-sfn-extract=bin.sfn_extract:cli'
        ],
    },
    install_requires=[
         "boto3>=1.14",
         "click>=7.1",
         "aws-parsecf>=1.1"
         "aws-cdk-core>=1.68",
         "aws-cdk-aws-iam",
         "aws-cdk-aws-s3",
         "aws-cdk-aws-lambda",
         "aws-cdk-aws-ssm",
         "aws-cdk-aws-secretsmanager"
   ],
    extras_require={
        "cicd": [
            "aws-cdk-aws-cloudformation",
            "aws-cdk-aws-codebuild",
            "aws-cdk-aws-codecommit",
            "aws-cdk-aws-codepipeline",
            "aws-cdk-aws-codepipeline-actions",
            "aws-cdk-aws-codestarconnections",
            "pyyaml"
        ],
        "nextstep": [
            "aws-cdk-aws-stepfunctions",
            "aws-cdk-aws-stepfunctions-tasks"
        ],
        "data": ["aws-cdk-glue", "aws-cdk-athena"]
    },
    python_requires='>=3.6',
)
