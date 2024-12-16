#!/usr/bin/env python3
#
# Pass directories or yaml files as arguments to validate sc4pac yaml files.

import yaml
import sys
import os
import re
from urllib.parse import (urlparse, parse_qs)
import jsonschema
from jsonschema import ValidationError

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

# Add packages as necessary. These packages should only be used as dependencies
# from packages with a matching variant. For example, a package without a DN
# variant should never depend on simfox:day-and-nite-mod.
variant_specific_dependencies = {
    "simfox:day-and-nite-mod": ("nightmode", "dark"),
    "toroca:industry-quadrupler": ("toroca:industry-quadrupler:capacity", "quadrupled"),
    "cam:colossus-addon-mod": ("CAM", "yes"),
}

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
        "url": {"type": "string", "validate_query_params": True},
        "nonPersistentUrl": {"type": "string", "validate_query_params": True},
        "archiveType": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "format": {"enum": ["Clickteam"]},
                "version": {"enum": ["20", "24", "30", "35", "40"]},
            },
        },
        "checksum": {
            "type": "object",
            "additionalProperties": False,
            "required": ["sha256"],
            "properties": {
                "sha256": {"type": "string", "validate_sha256": True},
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
            "include": {**unique_strings, "validate_pattern": True},
            "exclude": {**unique_strings, "validate_pattern": True},
            "withChecksum": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["include", "sha256"],
                    "properties": {
                        "include": {"type": "string", "validate_pattern": True},
                        "sha256": {"type": "string", "validate_sha256": True},
                    },
                },
                "uniqueItems": True,
            },
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
        "name": {"type": "string", "validate_name": True},
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
                "warning": {"type": "string", "validate_text_field": "warning"},
                "conflicts": {"type": "string", "validate_text_field": "conflicts"},
                "description": {"type": "string", "validate_text_field": "description"},
                "author": {"type": "string"},
                "images": unique_strings,
                "website": {"type": "string", "validate_query_params": True},
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
    sha256_pattern = re.compile(r"[a-f0-9]*", re.IGNORECASE)

    def __init__(self):
        self.known_packages = set()
        self.known_assets = set()
        self.referenced_packages = set()
        self.referenced_assets = set()
        self.self_dependencies = set()
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
        self.dlls_without_checksum = set()
        self.http_without_checksum = set()
        self.unexpected_variant_specific_dependencies = []  # (pkg, dependency)

    def aggregate_identifiers(self, doc):
        if 'assetId' in doc:
            asset = doc['assetId']
            if asset not in self.known_assets:
                self.known_assets.add(asset)
            else:
                self.duplicate_assets.add(asset)
            url = doc.get('url')
            self.asset_urls[asset] = url
            self.asset_versions[asset] = doc.get('version')
            if not self.naming_convention.fullmatch(asset):
                self.invalid_asset_names.add(asset)
            if urlparse(url).scheme not in ['https', 'file'] and 'checksum' not in doc:
                self.http_without_checksum.add(asset)
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

            variants0 = doc.get('variants', [])
            def iterate_doc_and_variants():
                yield doc
                yield from variants0

            for obj in iterate_doc_and_variants():
                local_deps = obj.get('dependencies', [])
                self.referenced_packages.update(local_deps)
                for dep in local_deps:
                    if dep == pkg:
                        self.self_dependencies.add(pkg)
                    if dep in variant_specific_dependencies:
                        expected_variant, expected_value = variant_specific_dependencies[dep]
                        if obj.get('variant', {}).get(expected_variant) != expected_value:
                            self.unexpected_variant_specific_dependencies.append((pkg, dep))

                local_assets = list(asset_ids(obj))
                self.referenced_assets.update(local_assets)
                for a in local_assets:
                    if a in self.packages_using_asset:
                        self.packages_using_asset[a].add(pkg)
                    else:
                        self.packages_using_asset[a] = set([pkg])

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

            is_dll = ("DLL" in doc.get('info', {}).get('summary', "")) or ("dll" in doc['name'].split('-'))
            if is_dll:
                has_asset = False
                has_checksum = False
                for obj in iterate_doc_and_variants():
                    for asset in obj.get('assets', []):
                        has_asset = True
                        if "withChecksum" in asset:
                            has_checksum = True
                if has_asset and not has_checksum:
                    self.dlls_without_checksum.add(pkg)


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


def validate_pattern(validator, value, instance, schema):
    patterns = [instance] if isinstance(instance, str) else instance
    bad_patterns = [p for p in patterns if p.startswith('.*')]
    if bad_patterns:
        yield ValidationError(f"include/exclude patterns should not start with '.*' in {bad_patterns}")


_irrelevant_query_parameters = [
    ("sc4evermore.com", ("catid",)),
    ("simtropolis.com", ("confirm", "t", "csrfKey")),
]


def validate_query_params(validator, value, url, schema):
    msgs = []
    if '/sc4evermore.com/' in url:
        msgs.append(f"Domain of URL {url} should be www.sc4evermore.com (add www.)")
    qs = parse_qs(urlparse(url).query)
    bad_params = [p for domain, params in _irrelevant_query_parameters
                  if domain in url for p in params if p in qs]
    if bad_params:
        msgs.append(f"Avoid these URL query parameters: {', '.join(bad_params)}")
    if msgs:
        yield ValidationError('\n'.join(msgs))


def validate_name(validator, value, name, schema):
    if "-vol-" in name:
        yield ValidationError(f"Avoid the hyphen after 'vol' (for consistency with other packages): {name}")


def validate_text_field(validator, field, text, schema):
    msgs = []
    if text is not None and text.strip().lower() == "none":
        msgs.append(f"""Text "{field}" should not be "{text.strip()}", but should be omitted instead.""")
    if text is not None and DependencyChecker.pronouns_pattern.search(text):
        msgs.append(f"""The "{field}" should be written in a neutral perspective (avoid the words 'I', 'me', 'my').""")
    if text is not None and DependencyChecker.desc_invalid_chars_pattern.search(text):
        msgs.append("""The "{field}" seems to be malformed (avoid the characters '\\n', '\\"').""")
    if msgs:
        yield ValidationError('\n'.join(msgs))


def validate_sha256(validator, value, text, schema):
    if not (len(text) == 64 and DependencyChecker.sha256_pattern.fullmatch(text)):
        yield ValidationError(f"value is not a sha256: {text}")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        "Pass at least one directory or yaml file to validate as argument."
        return 1

    validator = jsonschema.validators.extend(
            jsonschema.validators.Draft202012Validator,
            validators=dict(
                validate_pattern=validate_pattern,
                validate_query_params=validate_query_params,
                validate_name=validate_name,
                validate_text_field=validate_text_field,
                validate_sha256=validate_sha256,
            ),
        )(schema)
    validator.check_schema(schema)
    dependency_checker = DependencyChecker()
    validated = 0
    errors = 0

    def basic_report(identifiers, msg: str, stringify=None):
        if identifiers:
            nonlocal errors
            errors += len(identifiers)
            print(f"===> {msg}")
            for identifier in identifiers:
                print(identifier if stringify is None else stringify(identifier))

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
                            err = jsonschema.exceptions.best_match(validator.iter_errors(doc))
                            msgs = [] if err is None else [err.message]

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
            basic_report(unknown, f"The following {label} are referenced, but not defined:")
        for label, dupes in dependency_checker.duplicates().items():
            basic_report(dupes, f"The following {label} are defined multiple times:")
        basic_report(dependency_checker.self_dependencies, "The following packages unnecessarily depend on themselves:")
        basic_report(dependency_checker.unexpected_variant_specific_dependencies, "The following packages have dependencies that should only be used with specific variants:",
                     lambda tup: "{0} depends on {1}, but this dependency should only be used with variant \"{2}={3}\"".format(*(tup + variant_specific_dependencies[tup[1]])))
        basic_report(dependency_checker.assets_with_same_url(),
                     "The following assets have the same URL (The same asset was defined twice with different asset IDs):",
                     lambda assets: ', '.join(assets))
        basic_report(dependency_checker.unused_assets(), "The following assets are not used:")
        basic_report(dependency_checker.overlapping_variants, "The following packages have duplicate variants:")
        basic_report(dependency_checker.unexpected_variants, "",
                     lambda tup: "{0} defines unexpected {1} variants {2} (expected: {3})".format(*tup))  # pkg, key, values, expected_values
        basic_report(dependency_checker.invalid_asset_names, "the following assetIds do not match the naming convention (lowercase alphanumeric hyphenated)")
        basic_report(dependency_checker.invalid_group_names, "the following group identifiers do not match the naming convention (lowercase alphanumeric hyphenated)")
        basic_report(dependency_checker.invalid_package_names, "the following package names do not match the naming convention (lowercase alphanumeric hyphenated)")
        basic_report(dependency_checker.invalid_variant_names, "the following variant labels or values do not match the naming convention (alphanumeric hyphenated or dots)")
        basic_report(list(dependency_checker.package_asset_version_mismatches()),
                     "The versions of the following packages do not match the version of the referenced assets (usually they should agree, but if the version mismatch is intentional, the packages can be added to the ignore list in .github/sc4pac-yaml-schema.py):",
                     lambda tup: """{0} "{1}" (expected version "{3}" of asset {2})""".format(*tup))  # pkg, v1, asset, v2
        basic_report(dependency_checker.dlls_without_checksum, "The following packages appear to contain DLLs. A sha256 checksum is required for DLLs (add a `withChecksum` field).")
        basic_report(dependency_checker.http_without_checksum, "The following assets use http instead of https. They should include a `checksum` field.")

    if errors > 0:
        print(f"Finished with {errors} errors.")
        return 1
    else:
        print(f"Successfully validated {validated} files.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
