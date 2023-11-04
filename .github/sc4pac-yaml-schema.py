#!/usr/bin/env python3
#
# Pass directories or yaml files as arguments to validate sc4pac yaml files.

import yaml
import sys
import os

# add subfolders as necessary
subfolders = [
    "050-early-mods",
    "100-props-textures",
    "150-mods",
    "170-terrain",
    "180-flora",
    "200-residential",
    "300-commercial",
    "400-industrial",
    "500-utilities",
    "600-civics",
    "650-parks",
    "700-transit",
    "900-overrides",
]

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


def main() -> int:
    args = sys.argv[1:]
    if not args:
        "Pass at least one directory or yaml file to validate as argument."
        return 1

    from jsonschema.validators import Draft202012Validator
    from jsonschema import exceptions
    validator = Draft202012Validator(schema)
    validator.check_schema(schema)
    validated = 0
    errors = 0
    for d in args:
        for (root, dirs, files) in os.walk(d):
            for fname in files:
                if not fname.endswith(".yaml"):
                    continue
                p = os.path.join(root, fname)
                with open(os.path.join(root, fname)) as f:
                    validated += 1
                    text = f.read()
                    for doc in yaml.safe_load_all(text):
                        err = exceptions.best_match(validator.iter_errors(doc))
                        if err is not None:
                            errors += 1
                            print(f"===> {p}")
                            print(err.message)
    if errors > 0:
        print(f"Finished with {errors} errors.")
        return 1
    else:
        print(f"Successfully validated {validated} files.")
        return 0


if __name__ == '__main__':
    sys.exit(main())
