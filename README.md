# AVIV CDK for Python

A set of AWS CDK examples and constructs.

## Install

Requires:

- Python >= 3.6
- pip
- cdk >= 1.68
- access to AWS

In a terminal:

```sh
pip install aviv-cdk
```

## Develop

```sh
git clone https://github.com/aviv-group/aviv-cdk-python
pipenv install -d -e .
```

### Use it

```sh
# Build layer for release
pip install -r lambdas/cfn_resources/requirements.txt -t build/layers/cfn_resources/

# Or with codebuild agent - see: buildspec.yml
codebuild_build.sh -i aws/codebuild/standard:4.0 -a build
```

## Distrib & release

```sh
python3 setup.py sdist bdist_wheel
# test distrib
python3 -m twine upload --repository testpypi dist/*
```

## Contribute

Yes please! Fork this project, tweak it and share it back by sending your PRs.  
Have a look at the [TODO's](TODO) and [changelog](CHANGELOG) file if you're looking for inspiration.

## License

This project is developed under the [MIT license](license).

## Author(s) and Contributors

- Jules Clement \<jules.clement@aviv-group.com>
