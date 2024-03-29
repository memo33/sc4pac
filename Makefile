# Call this script with the correct path to `sc4pac`, e.g.:
#
#   make SC4PAC=./sc4pac-tools/sc4pac pages

# SC4PAC=sc4pac
SC4PAC=./sc4pac-tools/sc4pac

# Rebuild all .json files, the main.js file and update the gh-pages branch.
# On the first run, this sets up a worktree `gh-pages` checked out at ./gh-pages/
# and clones the project `sc4pac-tools` to ./sc4pac-tools/ and builds the `sc4pac` executable.
# On subsequent runs, this assumes that the executable has already been built manually and is up-to-date.
pages: lint | gh-pages sc4pac-tools
	cd ./gh-pages/ && git rm --quiet -rf --ignore-unmatch ./channel/ ./*.md ./index.html
	$(MAKE) channel
	cd ./sc4pac-tools/ && sbt web/fullLinkJS
	cp -p ./sc4pac-tools/web/target/scala-3.3.0/sc4pac-web-opt/main.js ./gh-pages/channel/
	cp -p ./sc4pac-tools/web/channel/{styles.css,index.html} ./gh-pages/channel/
	cp -p ./docs/index.html ./docs/*.md ./docs/.nojekyll ./gh-pages/
	cd ./gh-pages/ && git add ./channel ./index.html ./*.md ./.nojekyll && git commit --quiet --amend --no-edit

# Initially create gh-pages worktree directory.
# (not PHONY)
gh-pages:
	git worktree add gh-pages gh-pages

# Initially create sc4pac-tools repo directory and build executable.
# (not PHONY)
sc4pac-tools:
	git clone https://github.com/memo33/sc4pac-tools.git ./sc4pac-tools
	cd ./sc4pac-tools && sbt assembly

channel:
	$(SC4PAC) channel build --output ./gh-pages/channel/ ./src/yaml/

# Open e.g. http://localhost:8091/channel/?pkg=memo:essential-fixes
host:
	cd ./gh-pages/ && python -m http.server 8091

# This is useful for live-editing the markdown files.
host-docs:
	cd ./docs/ && python -m http.server 8091

lint:
	python .github/sc4pac-yaml-schema.py src/yaml

sc4e-check-updates:
	python .github/sc4e-check-updates.py src/yaml

.PHONY: pages channel host host-docs lint sc4e-check-updates
