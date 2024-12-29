#!/usr/bin/env python3
#
# Checks whether any assets on SC4E are newer than stated in our yaml files.
#
# Pass directories or yaml files as arguments.

# TODO incorporate this script into sc4pac-actions

import yaml
import sys
import os
import re
from dateutil.parser import isoparse
from datetime import timezone
import urllib.request
import json

url_id_pattern = re.compile(r".*sc4evermore.com/.*[?&]id=(\d+):.*")


def nonempty_docs(dirs_or_files):
    # Generate all the paths with non-empty documents contained in the yaml files.
    # Yield (path, None) in case of parse error.
    for d in dirs_or_files:
        paths = [d] if not os.path.isdir(d) else \
            (os.path.join(root, fname) for (root, dirs, files) in os.walk(d) for fname in files)
        for path in paths:
            if not path.endswith(".yaml"):
                continue
            with open(path, encoding='utf-8') as f:
                text = f.read()
                try:
                    for doc in yaml.safe_load_all(text):
                        if doc is None:  # empty yaml file or document
                            continue
                        yield path, doc
                except yaml.parser.ParserError:
                    path, None


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Pass at least one directory or yaml file to validate as argument.")
        return 1

    req = urllib.request.Request("https://www.sc4evermore.com/latest-modified-downloads.php", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as data:
        report = json.load(data)
        upstream_state = {str(item['id']): item for item in report['files']}

    errors = 0
    out_of_date = 0
    up_to_date = 0
    for p, doc in nonempty_docs(args):
        if doc is None:  # parse error
            errors += 1
            continue

        # check URLs
        url = doc.get('nonPersistentUrl') or doc.get('url')
        if url is None:
            continue  # not an asset
        m = url_id_pattern.fullmatch(url)
        if not m:
            continue  # we only check SC4E files
        file_id = m.group(1)

        last_modified_upstream = isoparse(upstream_state[file_id]['modified'])
        if last_modified_upstream.tzinfo is None:
            last_modified_upstream = last_modified_upstream.replace(tzinfo=timezone.utc)

        if 'lastModified' not in doc:
            errors += 1  # TODO
        else:
            last_modified = isoparse(doc.get('lastModified'))
            if last_modified == last_modified_upstream:
                up_to_date += 1
            else:
                if last_modified < last_modified_upstream:
                    out_of_date += 1
                else:
                    errors += 1  # our assets should not be newer than upstream's assets TODO
                    print("error: ", end='')
                print(f"{doc.get('assetId')}:")
                print(f"  {doc.get('version')} -> {upstream_state[file_id].get('release')}")
                print(f"  {last_modified.isoformat().replace('+00:00', 'Z')} -> {last_modified_upstream.isoformat().replace('+00:00', 'Z')}")
                print(f"  https://www.sc4evermore.com/index.php/downloads/download/{file_id}")
                print(f"  {p}")

    result = 0
    if out_of_date == 0:
        print(f"All {up_to_date} SC4E assets are up-to-date.")
    else:
        print(f"There are {out_of_date} outdated SC4E assets, while {up_to_date} are up-to-date.")
        result |= 0x02
    if errors > 0:
        print(f"Finished with {errors} errors.")
        result |= 0x01
    return result


if __name__ == '__main__':
    sys.exit(main())
