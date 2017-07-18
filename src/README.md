# OpsBot Lambda codebase

Built on Gordon, a framework for building and deploying AWS Lambda functions, refer https://gordon.readthedocs.io/en/latest/

# *settings.yml* contains the project configuration along with common property references
# *parameters* folder contains the common properties required for the lambda functions including elasticsearch host, port and slack token value
# *<lambda>/settings.yml* contains the app/lambda function level configuration, including build commands

## To build
```bash
$ gordon build
```

## To deploy
```bash
$ gordon apply
```
