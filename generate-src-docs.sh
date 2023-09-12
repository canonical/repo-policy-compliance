#!/usr/bin/env bash

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

rm -rf src-docs
# There is a problem with lazydocs and using the flask Blueprint class which is causing an error,
# skip that file
PYTHON_FILES=$(find repo_policy_compliance -name "*.py" -not -path "**/blueprint.py")
echo $PYTHON_FILES
lazydocs --no-watermark --output-path src-docs $PYTHON_FILES
