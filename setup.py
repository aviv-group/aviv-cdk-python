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
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(include=['aviv_cdk']),
    data_files=[
        ("share/aviv-cdk/cfn-resources", ["lambdas/cfn_resources/requirements.txt"]),
        ("share/aviv-cdk/iam-idp", [
            "lambdas/iam_idp/saml.py",
            "buildspec-iam-idp.yml",
            "lambdas//cfn_resources/requirements.txt"
        ])
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'aviv-aws=aviv_cdk.bin.aws_local:cli',
            'aviv-cdk-sfn-extract=aviv_cdk.bin.sfn_extract:cli'
        ],
    },
    install_requires=[
         "boto3>=1.14",
         "click>=7.1",
         "aws-parsecf>=1.1"
         "aws-cdk-core>=1.85",
         "aws-cdk-aws-iam>=1.85",
         "aws-cdk-aws-s3>=1.85",
         "aws-cdk-aws-lambda>=1.85",
         "aws-cdk-aws-events>=1.85",
         "aws-cdk-aws-events-targets>=1.85",
         "aws-cdk-aws-ssm>=1.85",
         "aws-cdk-aws-secretsmanager>=1.85"
   ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],

    extras_require={
        "cicd": [
            "aws-cdk-aws-cloudformation",
            "aws-cdk-aws-codebuild",
            "aws-cdk-aws-codecommit",
            "aws-cdk-aws-codepipeline",
            "aws-cdk-aws-codepipeline-actions",
            "aws-cdk-aws-codestarconnections",
            "aws-cdk-pipelines",
            "pyyaml>=5.3.1"
        ],
        "nextstep": [
            "aws-cdk-aws-stepfunctions",
            "aws-cdk-aws-stepfunctions-tasks"
        ],
        "data": [
            "aws-cdk-glue",
            "aws-cdk-athena"
        ]
    },
    python_requires='>=3.6',
    use_2to3=False,
    zip_safe=False
)
