# vim: set noet sw=4 ts=4 fileencoding=utf-8:
#
# Copyright (c) 2013 Dave Hughes <dave@waveform.org.uk>
# Copyright (c) 2013 Mime Consulting <info@mimeconsulting.co.uk>
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# External utilities
PYTHON=python
PYFLAGS=
DEST_DIR=/

# Calculate the base names of the distribution, the location of all source,
# documentation, packaging, icon, and executable script files
NAME:=$(shell $(PYTHON) $(PYFLAGS) setup.py --name)
VER:=$(shell $(PYTHON) $(PYFLAGS) setup.py --version)
PYVER:=$(shell $(PYTHON) $(PYFLAGS) -c "import sys; print 'py%d.%d' % sys.version_info[:2]")
PY_SOURCES:=$(shell \
	$(PYTHON) $(PYFLAGS) setup.py egg_info >/dev/null 2>&1 && \
	cat $(NAME).egg-info/SOURCES.txt)
DOC_SOURCES:=$(wildcard docs/*.rst)
DEB_SOURCES:=debian/changelog \
	debian/control \
	debian/copyright \
	debian/docs \
	debian/compat \
	debian/rules
LICENSES:=LICENSE.txt

# Calculate the name of all outputs
DIST_EGG=dist/$(NAME)-$(VER)-$(PYVER).egg
DIST_RPM=dist/$(NAME)-$(VER)-1.src.rpm
DIST_TAR=dist/$(NAME)-$(VER).tar.gz
DIST_DEB=dist/$(NAME)_$(VER)-1~ppa1_all.deb


# Default target
all:
	@echo "make install - Install on local system"
	@echo "make develop - Install symlinks for development"
	@echo "make test - Run tests through nose environment"
	@echo "make doc - Generate HTML and PDF documentation"
	@echo "make source - Create source package"
	@echo "make egg - Generate a PyPI egg package"
	@echo "make rpm - Generate an RedHat package"
	@echo "make deb - Generate a Debian package"
	@echo "make dist - Generate all packages"
	@echo "make clean - Get rid of all generated files"
	@echo "make release - Create and tag a new release"
	@echo "make upload - Upload the new release to repositories"

install: $(SUBDIRS)
	$(PYTHON) $(PYFLAGS) setup.py install --root $(DEST_DIR)

doc: $(DOC_SOURCES)
	$(PYTHON) $(PYFLAGS) setup.py build_sphinx -b html
	$(PYTHON) $(PYFLAGS) setup.py build_sphinx -b latex
	$(MAKE) -C build/sphinx/latex all-pdf

source: $(DIST_TAR) $(DIST_ZIP)

egg: $(DIST_EGG)

rpm: $(DIST_RPM)

deb: $(DIST_DEB)

dist: $(DIST_EGG) $(DIST_RPM) $(DIST_DEB) $(DIST_TAR) $(DIST_ZIP)

develop: tags
	$(PYTHON) $(PYFLAGS) setup.py develop

test:
	$(PYTHON) $(PYFLAGS) setup.py test

clean:
	$(PYTHON) $(PYFLAGS) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -fr build/ dist/ $(NAME).egg-info/ tags
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir clean; \
	done
	find $(CURDIR) -name "*.pyc" -delete

tags: $(PY_SOURCES)
	ctags -R --exclude="build/*" --exclude="debian/*" --exclude="windows/*" --exclude="docs/*" --languages="Python"

$(DIST_TAR): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats gztar

$(DIST_ZIP): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats zip

$(DIST_EGG): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py bdist_egg

$(DIST_RPM): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py bdist_rpm \
		--source-only \
		--doc-files README.rst,LICENSE.txt \
		--requires python

$(DIST_DEB): $(PY_SOURCES) $(DEB_SOURCES) $(SUBDIRS) $(LICENSES)
	# build the source package in the parent directory then rename it to
	# project_version.orig.tar.gz
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -b -i -I -Idist -Idocs -Ibuild/sphinx/doctrees -rfakeroot
	mkdir -p dist/
	cp ../$(NAME)_$(VER)-1~ppa1_all.deb dist/

release: $(PY_SOURCES) $(DOC_SOURCES) $(DEB_SOURCES)
	$(MAKE) clean
	# ensure there are no current uncommitted changes
	test -z "$(shell git status --porcelain)"
	# update the changelog with new release information
	dch --newversion $(VER)-1~ppa1 --controlmaint
	# commit the changes and add a new tag
	git commit debian/changelog -m "Updated changelog for release $(VER)"
	git tag -s release-$(VER) -m "Release $(VER)"

upload: $(PY_SOURCES) $(DOC_SOURCES) $(DEB_SOURCES) $(SUBDIRS) $(LICENSES)
	# build a source archive and upload to PyPI
	$(PYTHON) $(PYFLAGS) setup.py sdist upload
	# build the deb source archive and upload to the PPA
	$(PYTHON) $(PYFLAGS) setup.py build_sphinx -b man
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -S -i -I -Idist -Idocs -Ibuild/sphinx/doctrees -rfakeroot
	dput waveform-ppa ../$(NAME)_$(VER)-1~ppa1_source.changes

.PHONY: all install develop test doc source egg rpm deb dist clean tags release upload

