# vim: set noet sw=4 ts=4:

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
MSI_SOURCES:=windows/configure_spec.py \
	windows/template.spec \
	windows/configure_wxs.py \
	windows/template.wxs
DEB_SOURCES:=debian/changelog \
	debian/control \
	debian/copyright \
	debian/install \
	debian/rules \
	debian/source/include-binaries \
	debian/$(NAME).manpages \
	$(wildcard debian/*.desktop)
LICENSES:=LICENSE.txt LICENSE.rtf
SUBDIRS:=icons $(NAME)/windows/fallback-theme

# Calculate path names for remote builds
ROOT_SOURCE:=$(CURDIR)
ROOT_TARGET:=$(notdir $(ROOT_SOURCE))

# Calculate the name of all outputs
DIST_EGG=dist/$(NAME)-$(VER)-$(PYVER).egg
DIST_RPM=dist/$(NAME)-$(VER)-1.src.rpm
DIST_TAR=dist/$(NAME)-$(VER).tar.gz
DIST_MSI=dist/$(NAME)-$(VER).msi
DIST_DEB=dist/$(NAME)_$(VER)-1~ppa1_all.deb
MAN_DIR=build/sphinx/man
MAN_PAGES=$(MAN_DIR)/rasextract.1 $(MAN_DIR)/rasdump.1 $(MAN_DIR)/rasinfo.1


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
	@echo "make msi - Generate a Windows package"
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

msi: $(DIST_MSI)

dist: $(DIST_EGG) $(DIST_RPM) $(DIST_DEB) $(DIST_TAR) $(DIST_ZIP) $(DIST_MSI)

develop: tags
	$(PYTHON) $(PYFLAGS) setup.py develop

test:
	nosetests

clean:
	$(PYTHON) $(PYFLAGS) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -fr build/ dist/ $(NAME).egg-info/ tags $(LICENSES)
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir clean; \
	done
	find $(CURDIR) -name "*.pyc" -delete

tags: $(PY_SOURCES)
	ctags -R --exclude="build/*" --exclude="debian/*" --exclude="windows/*" --exclude="docs/*" --languages="Python"

LICENSE.rtf: LICENSE.odt
	unoconv -d document -f rtf --stdout $< > $@

$(SUBDIRS):
	$(MAKE) -C $@

$(MAN_PAGES): $(DOC_SOURCES)
	$(PYTHON) $(PYFLAGS) setup.py build_sphinx -b man

$(DIST_TAR): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats gztar

$(DIST_ZIP): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py sdist --formats zip

$(DIST_EGG): $(PY_SOURCES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py bdist_egg

$(DIST_RPM): $(PY_SOURCES) $(MAN_PAGES) $(SUBDIRS) $(LICENSES)
	$(PYTHON) $(PYFLAGS) setup.py bdist_rpm \
		--source-only \
		--doc-files README.rst,LICENSE.txt \
		--requires python
	# XXX Add man-pages to RPMs ... how?

$(DIST_DEB): $(PY_SOURCES) $(MAN_PAGES) $(DEB_SOURCES) $(SUBDIRS) $(LICENSES)
	# build the source package in the parent directory then rename it to
	# project_version.orig.tar.gz
	$(PYTHON) $(PYFLAGS) setup.py sdist --dist-dir=../
	rename -f 's/$(NAME)-(.*)\.tar\.gz/$(NAME)_$$1\.orig\.tar\.gz/' ../*
	debuild -b -i -I -Idist -Idocs -Ibuild/sphinx/doctrees -rfakeroot
	mkdir -p dist/
	cp ../$(NAME)_$(VER)-1~ppa1_all.deb dist/

$(DIST_MSI): $(PY_SOURCES) $(MSI_SOURCES) $(SUBDIRS) $(LICENSES)
	# build the MSI package on the remote winbuild instance (on EC2) then
	# copy it back to this machine (the script assumes winbuild has been
	# launched separately - see windows/winbuild)
	ssh winbuild "rm -fr $(ROOT_TARGET)/; mkdir $(ROOT_TARGET)"
	scp -Br $(ROOT_SOURCE)/* winbuild:$(ROOT_TARGET)/
	ssh winbuild "\
		cd $(ROOT_TARGET); \
		rm -fr windows/dist/; \
		python windows/configure_spec.py windows/template.spec windows/$(NAME).spec; \
		TEMP=/tmp python ../pyinstaller/utils/Build.py windows/$(NAME).spec; \
		python windows/configure_wxs.py windows/template.wxs windows/$(NAME).wxs; \
		candle -nologo -out windows/$(NAME).wixobj windows/$(NAME).wxs; \
		light -nologo -ext WixUIExtension -out dist/$(NAME)-$(VER).msi windows/$(NAME).wixobj"
	mkdir -p dist
	scp -B winbuild:$(ROOT_TARGET)/dist/$(NAME)-$(VER).msi $(ROOT_SOURCE)/dist

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
	# build the binary packages and upload them to the website
	$(MAKE) deb
	scp $(DIST_DEB) waveform:$(NAME)/downloads/
	ssh waveform "cd $(NAME)/downloads; md5sum $(notdir $(DIST_DEB)) > $(notdir $(DIST_DEB)).md5sum"
	ssh waveform "cd $(NAME)/downloads; sha1sum $(notdir $(DIST_DEB)) > $(notdir $(DIST_DEB)).sha1sum"
	$(MAKE) rpm
	scp $(DIST_RPM) waveform:$(NAME)/downloads/
	ssh waveform "cd $(NAME)/downloads; md5sum $(notdir $(DIST_RPM)) > $(notdir $(DIST_RPM)).md5sum"
	ssh waveform "cd $(NAME)/downloads; sha1sum $(notdir $(DIST_RPM)) > $(notdir $(DIST_RPM)).sha1sum"
	$(MAKE) egg
	scp $(DIST_EGG) waveform:$(NAME)/downloads/
	ssh waveform "cd $(NAME)/downloads; md5sum $(notdir $(DIST_EGG)) > $(notdir $(DIST_EGG)).md5sum"
	ssh waveform "cd $(NAME)/downloads; sha1sum $(notdir $(DIST_EGG)) > $(notdir $(DIST_EGG)).sha1sum"
	$(MAKE) msi
	scp $(DIST_MSI) waveform:$(NAME)/downloads/
	ssh waveform "cd $(NAME)/downloads; md5sum $(notdir $(DIST_MSI)) > $(notdir $(DIST_MSI)).md5sum"
	ssh waveform "cd $(NAME)/downloads; sha1sum $(notdir $(DIST_MSI)) > $(notdir $(DIST_MSI)).sha1sum"
	# fix the "-latest" redirect to point to the new packages
	ssh waveform "cd $(NAME)/downloads; sed -i -e '1,1 s/LATEST=.*$$/LATEST=$(VER)/' .htaccess"

.PHONY: all install develop test doc source egg rpm deb msi dist clean tags release upload $(SUBDIRS)

