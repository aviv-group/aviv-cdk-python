# AVIV CDK for Python

A set of AWS CDK examples and constructs.

## Install

Requires:

- Python >= 3.6
- pip

```sh
pip install aviv-cdk
```

Extras (provides additionnal libraries, in order to build some constructs):

- `cicd` - CDK codebuild/deploy
- `nextstep` - Stepfunctions & co
- `data` - data related stuff

```sh
pip install aviv-cdk[EXTRA]
```

## Build, distrib & release

_Requires __twine__ to be installed (`pip install twine`) and credentials to upload a new verison to pypi._

```sh
python3 setup.py sdist bdist_wheel
# test distrib
python3 -m twine upload --repository testpypi dist/*
```

## Included CDK apps / samples

### CICD

`cdk -a 'python3 cicd.py' ...`

_requires_:

- buildspec.yml

### IAM Idp

`cdk -a 'python3 app_idp.py' ...`

_requires_:

- cfn_resources.zip

## Command line tools

- [aviv-aws](bin/aws_local.py) (WIP)  
  Helper to run AWS stuff locally (CDK / SAM / StepFunctionsLocal)
- [aviv-cdk-sfn-extract](bin/sfn_extract.py)  
  Extract a StateMachine from a CFN template

## Develop and contribute :)

Requirements:

- Pipenv
- AWS cdk client
- [optional] docker
- [optional] AWS codebuild docker image (standard >= 4.0)

```sh
git clone https://github.com/aviv-group/aviv-cdk-python && cd aviv-cdk-python
pipenv install -d -e .
```

### Use it

```sh
# Build layer for release

pip install -r lambdas/cfn_resources/requirements.txt -t build/layers/cfn_resources/
(cd build/layers/cfn_resources/ &&  zip -q -r ../../artifacts-cfn_resources.zip .)

# Or with codebuild agent - see: buildspec.yml
codebuild_build.sh -i aws/codebuild/standard:4.0 -a build
```

### Test

Requires: pytest

```sh
pipenv run pytest -v tests/
```

## Contribute

Yes please! Fork this project, tweak it and share it back by sending your PRs.  
Have a look at the [TODO's](TODO) and [changelog](CHANGELOG) file if you're looking for inspiration.

## License

This project is developed under the [MIT license](license).

## Author(s) and Contributors

- Jules Clement \<jules.clement@aviv-group.com>
