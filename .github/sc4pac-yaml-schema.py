#!/usr/bin/env python3
#
# Pass directories or yaml files as arguments to validate sc4pac yaml files.

import yaml
import sys
import os
import re

# add subfolders as necessary
subfolders = r"""
### [subfolders-docsify]
050-load-first
100-props-textures
150-mods
170-terrain
180-flora
200-residential
300-commercial
360-landmark
400-industrial
410-agriculture
500-utilities
600-civics
610-safety
620-education
630-health
640-government
650-religion
660-parks
700-transit
710-automata
900-overrides
### [subfolders-docsify]
""".strip().splitlines()[1:-1]

# Add packages as necessary if the check for matching package and asset
# versions would otherwise fail and if there is a reason why the versions
# differ.
ignore_version_mismatches = set([
    "vortext:vortexture-1",
    "vortext:vortexture-2",
    "t-wrecks:industrial-revolution-mod-addon-set-i-d",
    "memo:industrial-revolution-mod",
    "bsc:mega-props-jrj-vol01",
    "bsc:mega-props-diggis-canals-streams-and-ponds",
    "bsc:mega-props-rubik3-vol01-wtc-props",
    "bsc:mega-props-newmaninc-rivers-and-ponds",
])

unique_strings = {
    "type": "array",
    "items": {"type": "string"},
    "uniqueItems": True,
}

map_of_strings = {
    "type": "object",
    "patternProperties": {".*": {"type": "string"}},
}

asset_schema = {
    "title": "Asset",
    "type": "object",
    "additionalProperties": False,
    "required": ["assetId", "version", "lastModified", "url"],
    "properties": {
        "assetId": {"type": "string"},
        "version": {"type": "string"},
        "lastModified": {"type": "string"},
        "url": {"type": "string"},
        "archiveType": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "format": {"enum": ["Clickteam"]},
                "version": {"enum": ["20", "24", "30", "35", "40"]},
            },
        },
    },
}

assets = {
    "type": "array",
    "items": {
        "type": "object",
        "additionalProperties": False,
        "required": ["assetId"],
        "properties": {
            "assetId": {"type": "string"},
            "include": unique_strings,
            "exclude": unique_strings,
        },
    },
}

package_schema = {
    "title": "Package",
    "type": "object",
    "additionalProperties": False,
    "required": ["group", "name", "version", "subfolder"],
    "properties": {
        "group": {"type": "string"},
        "name": {"type": "string"},
        "version": {"type": "string"},
        "subfolder": {"enum": subfolders},
        "dependencies": unique_strings,
        "assets": assets,
        "variants": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["variant"],
                "properties": {
                    "variant": map_of_strings,
                    "dependencies": unique_strings,
                    "assets": assets,
                },
            },
        },
        "variantDescriptions": {
            "type": "object",
            "patternProperties": {".*": map_of_strings},
        },
        "info": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "summary": {"type": "string"},
                "warning": {"type": "string"},
                "conflicts": {"type": "string"},
                "description": {"type": "string"},
                "author": {"type": "string"},
                "images": unique_strings,
                "website": {"type": "string"},
            },
        },
    },
}

schema = {
    "oneOf": [asset_schema, package_schema]
}

# if there are dependencies to packages in other channels, add those channels here
extra_channels = [
    # "https://memo33.github.io/sc4pac/channel/sc4pac-channel-contents.json",
]


class DependencyChecker:

    naming_convention = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
    naming_convention_variants_value = re.compile(r"[a-z0-9]+([-\.][a-z0-9]+)*", re.IGNORECASE)
    naming_convention_variants = re.compile(  # group:package:variant (regex groups: \1:\2:\3)
            rf"(?:({naming_convention.pattern}):)?(?:({naming_convention.pattern}):)?([a-zA-Z0-9]+(?:[-\.][a-zA-Z0-9]+)*)")
    version_rel_pattern = re.compile(r"(.*?)(-\d+)?")
    pronouns_pattern = re.compile(r"\b[Mm][ey]\b|(?:\bI\b(?!-|\.| [A-Z]))")
    desc_invalid_chars_pattern = re.compile(r'\\n|\\"')

    def __init__(self):
        self.known_packages = set()
        self.known_assets = set()
        self.referenced_packages = set()
        self.referenced_assets = set()
        self.duplicate_packages = set()
        self.duplicate_assets = set()
        self.asset_urls = {}  # asset -> url
        self.asset_versions = {}  # asset -> version
        self.overlapping_variants = set()
        self.known_variant_values = {}
        self.unexpected_variants = []
        self.invalid_asset_names = set()
        self.invalid_group_names = set()
        self.invalid_package_names = set()
        self.invalid_variant_names = set()
        self.packages_with_single_assets = {}  # pkg -> (version, set of assets from variants)
        self.packages_using_asset = {}  # asset -> set of packages

    def aggregate_identifiers(self, doc):
        if 'assetId' in doc:
            asset = doc['assetId']
            if asset not in self.known_assets:
                self.known_assets.add(asset)
            else:
                self.duplicate_assets.add(asset)
            self.asset_urls[asset] = doc.get('url')
            self.asset_versions[asset] = doc.get('version')
            if not self.naming_convention.fullmatch(asset):
                self.invalid_asset_names.add(asset)
        if 'group' in doc and 'name' in doc:
            pkg = doc['group'] + ":" + doc['name']
            if pkg not in self.known_packages:
                self.known_packages.add(pkg)
            else:
                self.duplicate_packages.add(pkg)
            if not self.naming_convention.fullmatch(doc['group']):
                self.invalid_group_names.add(doc['group'])
            if not self.naming_convention.fullmatch(doc['name']):
                self.invalid_package_names.add(doc['name'])

            def asset_ids(obj):
                return (a['assetId'] for a in obj.get('assets', []) if 'assetId' in a)

            def add_references(obj):
                self.referenced_packages.update(obj.get('dependencies', []))
                local_assets = list(asset_ids(obj))
                self.referenced_assets.update(local_assets)
                for a in local_assets:
                    if a in self.packages_using_asset:
                        self.packages_using_asset[a].add(pkg)
                    else:
                        self.packages_using_asset[a] = set([pkg])

            variants0 = doc.get('variants', [])
            add_references(doc)
            for v in variants0:
                add_references(v)

            num_doc_assets = len(doc.get('assets', []))
            if num_doc_assets <= 1:
                single_assets = set(asset_ids(doc))
                if all(len(v.get('assets', [])) <= 1 for v in variants0):
                    for v in variants0:
                        single_assets.update(asset_ids(v))
                    self.packages_with_single_assets[pkg] = (doc.get('version'), single_assets)

            variants = [v.get('variant', {}) for v in variants0]
            if len(variants) != len(set(tuple(sorted(v.items())) for v in variants)):
                # the same variant should not be defined twice
                self.overlapping_variants.add(pkg)

            variant_keys = set(key for v in variants for key, value in v.items())
            for key in variant_keys:
                variant_values = set(v[key] for v in variants if key in v)
                if key not in self.known_variant_values:
                    self.known_variant_values[key] = variant_values
                elif self.known_variant_values[key] != variant_values:
                    self.unexpected_variants.append((pkg, key, sorted(variant_values), sorted(self.known_variant_values[key])))
                else:
                    pass
                if not self.naming_convention_variants.fullmatch(key):
                    self.invalid_variant_names.add(key)
                for value in variant_values:
                    if not self.naming_convention_variants_value.fullmatch(value):
                        self.invalid_variant_names.add(value)

    def _get_channel_contents(self, channel_url):
        import urllib.request
        import json
        req = urllib.request.Request(channel_url)
        with urllib.request.urlopen(req) as data:
            channel_contents = json.load(data)
        return channel_contents['contents']

    def unknowns(self):
        packages = self.referenced_packages.difference(self.known_packages)
        assets = self.referenced_assets.difference(self.known_assets)
        if packages or assets:
            # some dependencies are not known, so check other channels
            contents = [self._get_channel_contents(channel_url) for channel_url in extra_channels]
            remote_assets = [pkg['name'] for c in contents for pkg in c if pkg['group'] == "sc4pacAsset"]
            remote_packages = [f"{pkg['group']}:{pkg['name']}" for c in contents for pkg in c if pkg['group'] != "sc4pacAsset"]
            packages = packages.difference(remote_packages)
            assets = assets.difference(remote_assets)
        return {'packages': sorted(packages), 'assets': sorted(assets)}

    def duplicates(self):
        return {'packages': sorted(self.duplicate_packages),
                'assets': sorted(self.duplicate_assets)}

    def assets_with_same_url(self):
        url_assets = {u: a for a, u in self.asset_urls.items()}
        non_unique_assets = [(a1, a2) for a1, u in self.asset_urls.items()
                             if (a2 := url_assets[u]) != a1]
        return non_unique_assets

    def unused_assets(self):
        return sorted(self.known_assets.difference(self.referenced_assets))

    # turns a patch version such as 1.0.0-2 into 1.0.0
    def _version_without_rel(self, version):
        return self.version_rel_pattern.fullmatch(version).group(1)

    def _should_expect_matching_version_for_asset(self, asset):
        # for assets used by more packages, we assume that the asset contains
        # multiple unrelated packages, so versions of packages do not need to match
        return len(self.packages_using_asset.get(asset, [])) <= 3

    def package_asset_version_mismatches(self):
        for pkg, (version, assets) in self.packages_with_single_assets.items():
            if pkg in ignore_version_mismatches:
                continue
            v1 = self._version_without_rel(version)
            for asset in assets:
                if self._should_expect_matching_version_for_asset(asset):
                    v2 = self._version_without_rel(self.asset_versions.get(asset, 'None'))
                    if v1 != v2:
                        yield (pkg, v1, asset, v2)


def validate_document_separators(text) -> None:
    needs_separator = False
    errors = 0
    for line in text.splitlines():
        if line.startswith("---"):
            needs_separator = False
        elif (line.startswith("group:") or line.startswith("\"group\":") or
              line.startswith("url:") or line.startswith("\"url\":")):
            if needs_separator:
                errors += 1
            else:
                needs_separator = True
        elif line.startswith("..."):
            break
    if errors > 0:
        raise yaml.parser.ParserError(
                "YAML file contains multiple package and asset definitions. They all need to be separated by `---`.")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        "Pass at least one directory or yaml file to validate as argument."
        return 1

    from jsonschema.validators import Draft202012Validator
    from jsonschema import exceptions
    validator = Draft202012Validator(schema)
    validator.check_schema(schema)
    dependency_checker = DependencyChecker()
    validated = 0
    errors = 0
    for d in args:
        for (root, dirs, files) in os.walk(d):
            for fname in files:
                if not fname.endswith(".yaml"):
                    continue
                p = os.path.join(root, fname)
                with open(p, encoding='utf-8') as f:
                    validated += 1
                    text = f.read()
                    try:
                        validate_document_separators(text)
                        for doc in yaml.safe_load_all(text):
                            if doc is None:  # empty yaml file or document
                                continue
                            dependency_checker.aggregate_identifiers(doc)
                            err = exceptions.best_match(validator.iter_errors(doc))
                            msgs = [] if err is None else [err.message]

                            # check URLs
                            urls = [u for u in [doc.get('url'), doc.get('info', {}).get('website')]
                                    if u is not None]
                            for u in urls:
                                if '/sc4evermore.com/' in u:
                                    msgs.append(f"Domain of URL {u} should be www.sc4evermore.com")

                            # check "None" value
                            for label in ['conflicts', 'warning', 'summary', 'description']:
                                field = doc.get('info', {}).get(label)
                                if field is not None and field.strip().lower() == "none":
                                    msgs.append(f"""Field "{label}" should not be "{field.strip()}", but should be left out instead.""")

                            desc = doc.get('info', {}).get('description')
                            if desc is not None and dependency_checker.pronouns_pattern.search(desc):
                                msgs.append("The description should be written in a neutral perspective (avoid the words 'I', 'me', 'my').")
                            if desc is not None and dependency_checker.desc_invalid_chars_pattern.search(desc):
                                msgs.append("""The description seems to be malformed (avoid the characters '\\n', '\\"').""")

                            if msgs:
                                errors += 1
                                print(f"===> {p}")
                                for msg in msgs:
                                    print(msg)
                    except yaml.parser.ParserError as err:
                        errors += 1
                        print(f"===> {p}")
                        print(err)

    if not errors:
        # check that all dependencies exist
        # (this check only makes sense for the self-contained main channel)
        for label, unknown in dependency_checker.unknowns().items():
            if unknown:
                errors += len(unknown)
                print(f"===> The following {label} are referenced, but not defined:")
                for identifier in unknown:
                    print(identifier)

        for label, dupes in dependency_checker.duplicates().items():
            if dupes:
                errors += len(dupes)
                print(f"===> The following {label} are defined multiple times:")
                for identifier in dupes:
                    print(identifier)

        non_unique_assets = dependency_checker.assets_with_same_url()
        if non_unique_assets:
            errors += len(non_unique_assets)
            print("===> The following assets have the same URL (The same asset was defined twice with different asset IDs):")
            for assets in non_unique_assets:
                print(', '.join(assets))

        unused_assets = dependency_checker.unused_assets()
        if unused_assets:
            errors += len(unused_assets)
            print("===> The following assets are not used:")
            for identifier in unused_assets:
                print(identifier)

        if dependency_checker.overlapping_variants:
            errors += len(dependency_checker.overlapping_variants)
            print("===> The following packages have duplicate variants:")
            for pkg in dependency_checker.overlapping_variants:
                print(pkg)

        if dependency_checker.unexpected_variants:
            errors += len(dependency_checker.unexpected_variants)
            print("===>")
            for pkg, key, values, expected_values in dependency_checker.unexpected_variants:
                print(f"{pkg} defines {key} variants {values} (expected: {expected_values})")

        if dependency_checker.invalid_asset_names:
            errors += len(dependency_checker.invalid_asset_names)
            print("===> the following assetIds do not match the naming convention (lowercase alphanumeric hyphenated)")
            for identifier in dependency_checker.invalid_asset_names:
                print(identifier)
        if dependency_checker.invalid_group_names:
            errors += len(dependency_checker.invalid_group_names)
            print("===> the following group identifiers do not match the naming convention (lowercase alphanumeric hyphenated)")
            for identifier in dependency_checker.invalid_group_names:
                print(identifier)
        if dependency_checker.invalid_package_names:
            errors += len(dependency_checker.invalid_package_names)
            print("===> the following package names do not match the naming convention (lowercase alphanumeric hyphenated)")
            for identifier in dependency_checker.invalid_package_names:
                print(identifier)
        if dependency_checker.invalid_variant_names:
            errors += len(dependency_checker.invalid_variant_names)
            print("===> the following variant labels or values do not match the naming convention (alphanumeric hyphenated or dots)")
            for identifier in dependency_checker.invalid_variant_names:
                print(identifier)

        version_mismatches = list(dependency_checker.package_asset_version_mismatches())
        if version_mismatches:
            errors += len(version_mismatches)
            print("===> The versions of the following packages do not match the version of the referenced assets (usually they should agree, but if the version mismatch is intentional, the packages can be added to the ignore list in .github/sc4pac-yaml-schema.py):")
            for pkg, v1, asset, v2 in version_mismatches:
                print(f"""{pkg} "{v1}" (expected version "{v2}" of asset {asset})""")

    if errors > 0:
        print(f"Finished with {errors} errors.")
        return 1
    else:
        print(f"Successfully validated {validated} files.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
