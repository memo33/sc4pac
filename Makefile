# Call this script with the correct path to `sc4pac`, e.g.:
#
#   make SC4PAC=./sc4pac-tools/sc4pac gh-pages

# SC4PAC=sc4pac
SC4PAC=./sc4pac-tools/sc4pac

# LABEL=Main
LABEL=Main-local

# assumes you have checked out sc4pac-actions in the same parent folder
ACTIONS=../sc4pac-actions

# Rebuild all .json files, the main.js file and update the gh-pages branch.
#
# This assumes that you have initialized the submodule `sc4pac-tools` with:
#
#     git submodule update --init --recursive
#
# And that you have an up-to-date `sc4pac` executable, for example created by:
#
#     cd sc4pac-tools && sbt assembly
#
gh-pages: lint gh-pages-no-lint

gh-pages-no-lint:
	rm -rf ./gh-pages/
	$(MAKE) channel
	cd ./sc4pac-tools/ && ./src/scripts/build-channel-page.sh
	cp -p ./sc4pac-tools/web/target/website/channel/* ./gh-pages/channel/
	cp -pr ./docs/. ./gh-pages/

channel:
	$(SC4PAC) channel build --label $(LABEL) --metadata-source-url https://github.com/memo33/sc4pac/blob/main/src/yaml/ --output ./gh-pages/channel/ ./src/yaml/

# Open e.g. http://localhost:8091/channel/?pkg=memo:essential-fixes
host:
	cd ./gh-pages/ && python -m http.server 8091

# This is useful for live-editing the markdown files.
host-docs:
	cd ./docs/ && python -m http.server 8091

lint:
	python $(ACTIONS)/src/lint.py src/yaml

sc4e-check-updates:
	python .github/sc4e-check-updates.py src/yaml

# First reads in the STEX_API_KEY from a file into an environment variable and then checks for asset updates using the authenticated STEX API.
st-check-updates:
	set -a && source ./.git/sc4pac-stex-api-key && set +a && python $(ACTIONS)/src/st-check-updates.py src/yaml

st-url-check:
	set -a && source ./.git/sc4pac-stex-api-key && set +a \
		&& git diff "$(shell git merge-base @ "origin/main")" --name-only -- "src/yaml" \
		| xargs --delimiter '\n' python $(ACTIONS)/src/st-check-updates.py --mode=id

.PHONY: gh-pages gh-pages-no-lint channel host host-docs lint sc4e-check-updates st-check-updates st-url-check
