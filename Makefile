# Call this script with the correct path to `sc4pac`, e.g.:
#
#   make SC4PAC=./sc4pac-tools/sc4pac gh-pages

# SC4PAC=sc4pac
SC4PAC=./sc4pac-tools/sc4pac

# Rebuild all .json files, the main.js file and update the gh-pages branch.
# This assumes that a worktree `gh-pages` is checked out at ./gh-pages/
# and that the project `sc4pac-tools` is checked out at ./sc4pac-tools/
gh-pages:
	cd ./gh-pages/ && git rm --quiet -rf ./channel/
	$(SC4PAC) channel build --output ./gh-pages/channel/ ./src/yaml/
	cd ./sc4pac-tools/ && sbt web/fullLinkJS
	cp -p ./sc4pac-tools/web/target/scala-3.3.0/sc4pac-web-opt/main.js ./gh-pages/channel/
	cp -p ./sc4pac-tools/web/channel/{styles.css,index.html} ./gh-pages/channel/
	cd ./gh-pages/ && git add channel && git commit --quiet --amend --no-edit

# Open e.g. http://localhost:8091/channel/?pkg=memo:essential-fixes
host:
	cd ./gh-pages/ && python -m http.server 8091

.PHONY: gh-pages
