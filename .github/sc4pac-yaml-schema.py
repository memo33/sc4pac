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
050-early-mods
100-props-textures
150-mods
170-terrain
180-flora
200-residential
300-commercial
360-landmark
400-industrial
500-utilities
600-civics
610-safety
620-education
630-health
640-government
650-religion
660-parks
700-transit
900-overrides
### [subfolders-docsify]
""".strip().splitlines()[1:-1]

uniqueStrings = {
    "type": "array",
    "items": {"type": "string"},
    "uniqueItems": True,
}

mapOfStrings = {
    "type": "object",
    "patternProperties": {".*": {"type": "string"}},
}

assetSchema = {
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
            "include": uniqueStrings,
            "exclude": uniqueStrings,
        },
    },
}

packageSchema = {
    "title": "Package",
    "type": "object",
    "additionalProperties": False,
    "required": ["group", "name", "version", "subfolder"],
    "properties": {
        "group": {"type": "string"},
        "name": {"type": "string"},
        "version": {"type": "string"},
        "subfolder": {"enum": subfolders},
        "dependencies": uniqueStrings,
        "assets": assets,
        "variants": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["variant"],
                "properties": {
                    "variant": mapOfStrings,
                    "dependencies": uniqueStrings,
                    "assets": assets,
                },
            },
        },
        "variantDescriptions": {
            "type": "object",
            "patternProperties": {".*": mapOfStrings},
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
                "images": uniqueStrings,
                "website": {"type": "string"},
            },
        },
    },
}

schema = {
    "oneOf": [assetSchema, packageSchema]
}


class DependencyChecker:

    naming_convention = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
    naming_convention_variants = re.compile(r"[a-z0-9]+([-\.][a-z0-9]+)*", re.IGNORECASE)

    def __init__(self):
        self.known_packages = set()
        self.known_assets = set()
        self.referenced_packages = set()
        self.referenced_assets = set()
        self.duplicate_packages = set()
        self.duplicate_assets = set()
        self.asset_urls = {}
        self.overlapping_variants = set()
        self.known_variant_values = {}
        self.unexpected_variants = []
        self.invalid_asset_names = set()
        self.invalid_group_names = set()
        self.invalid_package_names = set()
        self.invalid_variant_names = set()

    def aggregate_identifiers(self, doc):
        if 'assetId' in doc:
            asset = doc['assetId']
            if asset not in self.known_assets:
                self.known_assets.add(asset)
            else:
                self.duplicate_assets.add(asset)
            self.asset_urls[asset] = doc.get('url')
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

            def add_references(obj):
                self.referenced_packages.update(obj.get('dependencies', []))
                self.referenced_assets.update(
                        a['assetId'] for a in obj.get('assets', [])
                        if 'assetId' in a)

            variants0 = doc.get('variants', [])
            add_references(doc)
            for v in variants0:
                add_references(v)

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
                    if not self.naming_convention_variants.fullmatch(value):
                        self.invalid_variant_names.add(value)

    def unknowns(self):
        packages = sorted(self.referenced_packages.difference(self.known_packages))
        assets = sorted(self.referenced_assets.difference(self.known_assets))
        return {'packages': packages, 'assets': assets}

    def duplicates(self):
        return {'packages': sorted(self.duplicate_packages),
                'assets': sorted(self.duplicate_assets)}

    def assets_with_same_url(self):
        url_assets = {u: a for a, u in self.asset_urls.items()}
        non_unique_assets = [(a1, a2) for a1, u in self.asset_urls.items()
                             if (a2 := url_assets[u]) != a1]
        return non_unique_assets


def main() -> int:
    args = sys.argv[1:]
    if not args:
        "Pass at least one directory or yaml file to validate as argument."
        return 1

    from jsonschema.validators import Draft202012Validator
    from jsonschema import exceptions
    validator = Draft202012Validator(schema)
    validator.check_schema(schema)
    dependencyChecker = DependencyChecker()
    validated = 0
    errors = 0
    for d in args:
        for (root, dirs, files) in os.walk(d):
            for fname in files:
                if not fname.endswith(".yaml"):
                    continue
                p = os.path.join(root, fname)
                with open(p) as f:
                    validated += 1
                    text = f.read()
                    try:
                        for doc in yaml.safe_load_all(text):
                            dependencyChecker.aggregate_identifiers(doc)
                            err = exceptions.best_match(validator.iter_errors(doc))
                            msgs = [] if err is None else [err.message]

                            # check URLs
                            urls = [u for u in [doc.get('url'), doc.get('info', {}).get('website')]
                                    if u is not None]
                            for u in urls:
                                if '/sc4evermore.com/' in u:
                                    msgs.append(f"Domain of URL {u} should be www.sc4evermore.com")

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
        for label, unknown in dependencyChecker.unknowns().items():
            if unknown:
                errors += len(unknown)
                print(f"===> The following {label} are referenced, but not defined:")
                for identifier in unknown:
                    print(identifier)

        for label, dupes in dependencyChecker.duplicates().items():
            if dupes:
                errors += len(dupes)
                print(f"===> The following {label} are defined multiple times:")
                for identifier in dupes:
                    print(identifier)

        non_unique_assets = dependencyChecker.assets_with_same_url()
        if non_unique_assets:
            errors += len(non_unique_assets)
            print("===> The following assets have the same URL:")
            for assets in non_unique_assets:
                print(', '.join(assets))

        if dependencyChecker.overlapping_variants:
            errors += len(dependencyChecker.overlapping_variants)
            print("===> The following packages have duplicate variants:")
            for pkg in dependencyChecker.overlapping_variants:
                print(pkg)

        if dependencyChecker.unexpected_variants:
            errors += len(dependencyChecker.unexpected_variants)
            print("===>")
            for pkg, key, values, expected_values in dependencyChecker.unexpected_variants:
                print(f"{pkg} defines {key} variants {values} (expected: {expected_values})")

        if dependencyChecker.invalid_asset_names:
            errors += len(dependencyChecker.invalid_asset_names)
            print("===> the following assetIds do not match the naming convention (lowercase alphanumeric hyphenated)")
            for identifier in dependencyChecker.invalid_asset_names:
                print(identifier)
        if dependencyChecker.invalid_group_names:
            errors += len(dependencyChecker.invalid_group_names)
            print("===> the following group identifiers do not match the naming convention (lowercase alphanumeric hyphenated)")
            for identifier in dependencyChecker.invalid_group_names:
                print(identifier)
        if dependencyChecker.invalid_package_names:
            errors += len(dependencyChecker.invalid_package_names)
            print("===> the following package names do not match the naming convention (lowercase alphanumeric hyphenated)")
            for identifier in dependencyChecker.invalid_package_names:
                print(identifier)
        if dependencyChecker.invalid_variant_names:
            errors += len(dependencyChecker.invalid_variant_names)
            print("===> the following variant labels or values do not match the naming convention (alphanumeric hyphenated or dots)")
            for identifier in dependencyChecker.invalid_variant_names:
                print(identifier)

    if errors > 0:
        print(f"Finished with {errors} errors.")
        return 1
    else:
        print(f"Successfully validated {validated} files.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
