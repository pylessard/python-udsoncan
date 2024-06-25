#!/bin/bash
set -eEuo pipefail
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/.. >/dev/null 2>&1 && pwd -P )"
cd "$PROJECT_ROOT"

RED='\033[0;31m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m' 

info()  { >&2 echo -e "$CYAN[Info]$NC $1";}
warn()  { >&2 echo -e "$YELLOW[Warning]$NC $1";}
error() { >&2 echo -e "$RED[Error]$NC $1"; }
fatal() { >&2 echo -e "$RED[Fatal]$NC $1"; exit ${2:-1}; }

trap 'fatal "Exited with status $? at line $LINENO"' ERR 

[ -z ${1:+x} ] && fatal "Missing version argument"

version=$1

git_diff=$(git diff --shortstat)
git_diff_cached=$(git diff --shortstat --cached)

[ -z $git_diff ] || fatal "Uncomitted changes on repo"
[ -z $git_diff_cached ] || fatal "Staging changes on repo"

tag=$( { git tag -l --points-at HEAD || true; } | { grep $version || true; })
code_version=$(cat udsoncan/__init__.py | grep __version__  | sed -r "s/__version__[[:space:]]*=[[:space:]]*'([^']+)'/\1/")

[ "$version" != "$tag" ] && fatal "Tag of HEAD does not match given version. Expected '$version'"
[ "$version" != "v$code_version" ] && fatal "Code version does not match given version : 'v$code_version' vs '$version'"

rm -rf build dist *.egg-info
python3 -m build

read -p "Everything seems alright. Upload? "

proceed=0
 
[ "${REPLY,,}" == "yes" ] && proceed=1
[ "${REPLY,,}" == "y" ] && proceed=1

[ $proceed -ne 1 ] && { info "Not uploading"; exit; }
python3 -m twine upload dist/*
