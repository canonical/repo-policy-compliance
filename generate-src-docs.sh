#!/usr/bin/env bash

# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

rm -rf src-docs
# There is a problem with lazydocs and using the flask Blueprint class which is causing an error,
# skip that file
PYTHON_FILES=$(find repo_policy_compliance -name "*.py" -not -path "**/blueprint.py")
# The word splitting is intentional here
# shellcheck disable=SC2086
lazydocs --no-watermark --output-path src-docs $PYTHON_FILES
