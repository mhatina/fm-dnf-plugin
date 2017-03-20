#!/bin/bash
FM_ARGS="-c ./fm.cfg"
# These are valid for our, fm, testing repo:
# HTTPD_MODULE="httpd"
# HTTPD_MODULE_VERSION="2.2.15-1"
# HTTPD_MODULE_UPGRADED_VERSION="2.2.15-2"
# HTTPD_MODULE_UPGRADED_HTTPD_VERSION="2.2.15-2"
# HTTPD_MODULE_REBASED_VERSION="2.4.18"
# HTTPD_MODULE_REBASED_HTTPD_VERSION="2.4.18"
# HTTPD_MODULE_PROFILE=default

# These are valid for the modularity testing repos:
HTTPD_MODULE="fm-group:web-server"
HTTPD_MODULE_VERSION="24-1"
HTTPD_MODULE_UPGRADED_VERSION="24-2"
HTTPD_MODULE_UPGRADED_HTTPD_VERSION="2.4.23-4"
HTTPD_MODULE_REBASED_VERSION="25-1"
HTTPD_MODULE_REBASED_HTTPD_VERSION="2.4.23-4"

# As a user, I would like to use the F24 webserver yum group on my Rawhide VM have it perform normally.
# 
# AC:
# 
# DONE   allow a user to downgrade to the F24-webserver modules from rawhide
# DONE   smoke test the module for basic functionality
# ----   ensure the module tracks changes / updates to the f24 version of the module
#        - DONE PARTIALY - we do not have multiple httpd module versions in the official Flock repo,
#        but we do have that in testing fm repo.


echo "Test 1 - Downgrade httpd"

set -e
set -x

rm -rf ./test.cache.d/*
rm -rf /etc/yum.repos.d/_fm_*

# Remove all old versions of httpd just to be sure
dnf remove httpd httpd-tools -y >/dev/null || true

# Install httpd from the system to check the downgrade to module's version
dnf install httpd -y

# Basic tests to search/list/info the web-server module
fm $FM_ARGS search $HTTPD_MODULE|grep $HTTPD_MODULE >/dev/null
fm $FM_ARGS list|grep $HTTPD_MODULE >/dev/null
fm $FM_ARGS info $HTTPD_MODULE|grep "Name: $HTTPD_MODULE" > /dev/null

# Enable the web-server module
fm $FM_ARGS enable $HTTPD_MODULE-$HTTPD_MODULE_VERSION -y

# Install the httpd, it should be installed from the module and not from
# rawhide

if [ -z "$var" ]; then
    dnf repository-packages _fm_$HTTPD_MODULE install httpd --allowerasing -y
fi

dnf repository-packages _fm_$HTTPD_MODULE list installed|grep httpd.x86_64

# Start the httpd and test it
systemctl start httpd
curl http://localhost > /dev/null
systemctl stop httpd

# Run "dnf upgrade httpd" to be sure it does not get overwritten by the system repo
dnf upgrade httpd -y
dnf repository-packages _fm_$HTTPD_MODULE list installed|grep httpd.x86_64

# Check for the httpd upgrade
fm $FM_ARGS check-upgrade|grep "$HTTPD_MODULE"|grep "$HTTPD_MODULE_UPGRADED_VERSION"

# Upgrade the httpd module to latest release
fm $FM_ARGS upgrade $HTTPD_MODULE -y
rpm -q httpd|grep "httpd-$HTTPD_MODULE_UPGRADED_HTTPD_VERSION"

# Run "dnf upgrade httpd" to be sure it does not get overwritten by the system repo
dnf upgrade httpd -y
dnf repository-packages _fm_$HTTPD_MODULE list installed|grep httpd.x86_64

# Check for the httpd rebase
fm $FM_ARGS check-rebase|grep "$HTTPD_MODULE"|grep "$HTTPD_MODULE_REBASED_VERSION"

# Upgrade the httpd module to latest version
fm $FM_ARGS rebase $HTTPD_MODULE-$HTTPD_MODULE_REBASED_VERSION -y
rpm -q httpd|grep "httpd-$HTTPD_MODULE_REBASED_HTTPD_VERSION"

# Disable the httpd module
fm $FM_ARGS disable $HTTPD_MODULE
