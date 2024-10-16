# Call this script with the correct path to `sc4pac`, e.g.:
#
#   make SC4PAC=./sc4pac-tools/sc4pac gh-pages

# SC4PAC=sc4pac
SC4PAC=./sc4pac-tools/sc4pac

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
	cd ./sc4pac-tools/ && sbt web/fullLinkJS
	cp -p ./sc4pac-tools/web/target/scala-3.4.2/sc4pac-web-opt/main.js ./gh-pages/channel/
	cp -p ./sc4pac-tools/web/channel/styles.css ./sc4pac-tools/web/channel/index.html ./gh-pages/channel/
	cp -p ./docs/index.html ./docs/*.md ./docs/.nojekyll ./gh-pages/

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

# First reads in the STEX_API_KEY from a file into an environment variable and then checks for asset updates using the authenticated STEX API.
st-check-updates:
	set -a && source ./.git/sc4pac-stex-api-key && set +a && python .github/st-check-updates.py src/yaml

st-url-check:
	set -a && source ./.git/sc4pac-stex-api-key && set +a && sh .github/url-check.sh origin/main src/yaml

.PHONY: gh-pages gh-pages-no-lint channel host host-docs lint sc4e-check-updates st-check-updates st-url-check
