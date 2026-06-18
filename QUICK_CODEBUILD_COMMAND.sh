#!/bin/bash
# Quick one-liner version - run this in CloudShell

cd ~ && git clone https://github.com/AbilashEEG/rfp-management.git 2>/dev/null || cd rfp-management && bash CODEBUILD_ARM64_SETUP.sh
