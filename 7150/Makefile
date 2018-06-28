#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for burstmonitor extension
#
# useful targets:
#   make clean ----- cleans distutils
#   make pylint ---- source code checks
#   make rpm  ------ produce RPMs
#
########################################################
# variable section

NAME = "burstmonitor"

PYTHON=python
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

# VERSION file provides one place to update the software version
VERSION := $(shell cat VERSION)
RPMRELEASE := 1

# RPM build parameters
RPMSPECDIR = .
RPMSPEC = $(RPMSPECDIR)/burstmonitor.spec

########################################################

all: clean pylint rpm

pylint:
	find . -name \*.py | xargs pylint --rcfile .pylintrc

clean:
	@echo "---------------------------------------------"
	@echo "Cleaning up distutils stuff"
	@echo "---------------------------------------------"
	rm -rf build
	rm -rf dist
	rm -rf MANIFEST
	@echo "---------------------------------------------"
	@echo "Cleaning up rpmbuild stuff"
	@echo "---------------------------------------------"
	rm -rf rpmbuild
	@echo "---------------------------------------------"
	@echo "Cleaning up byte compiled python stuff"
	@echo "---------------------------------------------"
	find . -type f -regex ".*\.py[co]$$" -delete
	@echo "---------------------------------------------"
	@echo "Removing burstmonitor.egg-info"
	@echo "---------------------------------------------"
	rm -rf burstmonitor.egg-info

sdist: clean
	$(PYTHON) setup.py sdist

rpmcommon: sdist
	@mkdir -p rpmbuild
	@cp dist/*.gz rpmbuild/
	@sed -e 's#^Version:.*#Version: $(VERSION)#' \
	     -e 's#^Release:.*#Release: $(RPMRELEASE)#' $(RPMSPEC) > rpmbuild/$(NAME).spec

rpm: rpmcommon
	@rpmbuild --define "_topdir %(pwd)/rpmbuild" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir $(RPMSPECDIR)" \
	--define "_sourcedir %{_topdir}" \
	--define "_rpmfilename %%{NAME}-%%{VERSION}-%%{RELEASE}.rpm" \
	--define "__python /usr/bin/python" \
	-ba rpmbuild/$(NAME).spec
	@rm -f rpmbuild/$(NAME).spec
	@rm -f rpmbuild/*.src.rpm
	@echo "---------------------------------------------"
	@echo "burstmonitor RPM is built:"
	@echo "    rpmbuild/$(NAME)-$(VERSION)-$(RPMRELEASE).rpm"
	@echo "---------------------------------------------"
