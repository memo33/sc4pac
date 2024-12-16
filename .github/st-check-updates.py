#!/usr/bin/env python3
#
# Checks whether any assets on STEX are newer than stated in our yaml files,
# considering the last 180 days.
# The STEX_API_KEY environment variable must be set for authentication.
#
# Pass `--mode=id` as argument to query exactly the IDs used in asset URLs.
# Defaults to `--mode=updated` which queries for recently updated IDs only.
#
# Additionally, pass directories or yaml files as arguments.

import yaml
import sys
import os
import re
from dateutil.parser import isoparse
from datetime import timezone, timedelta
import urllib.request
import json

stex_api_key = os.environ.get('STEX_API_KEY')  # issued by ST admins
url_id_pattern = re.compile(r".*simtropolis.com/files/file/(\d+)-.*?(?:$|[?&]r=(\d+).*$)")  # matches ID and optional subfile ID
since_days = 180  # to keep the request small
id_limit = 250  # to keep the request small


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
    id_mode = any(a == "--mode=id" for a in args)  # instead of --mode=updated
    args = [a for a in args if not a.startswith("--")]
    if not args:
        print("Found no yaml files to analyze.")
        return 0

    if not stex_api_key:
        print("The STEX_API_KEY environment variable must be set for authentication.")
        return 1

    errors = 0
    if id_mode:
        file_ids = []
        for p, doc in nonempty_docs(args):
            if doc is None:  # parse error
                errors += 1
                continue

            # find all STEX file IDs
            url = doc.get('nonPersistentUrl') or doc.get('url')
            if url is None:
                continue  # not an asset
            m = url_id_pattern.fullmatch(url)
            if not m:
                continue  # we only check ST files
            file_id = m.group(1)
            file_ids.append(file_id)

        if not file_ids:
            print("No STEX file IDs found in yaml files.")
            return 0

        # check relevant STEX file IDs only
        req_url = f"https://community.simtropolis.com/stex/files-api.php?key={stex_api_key}&sort=desc&id=" + ",".join(file_ids[:id_limit])
    else:
        # check most recently updated STEX entries only
        req_url = f"https://community.simtropolis.com/stex/files-api.php?key={stex_api_key}&days={since_days}&mode=updated&sc4only=true&sort=desc"

    req = urllib.request.Request(req_url, headers={'User-Agent': 'Mozilla/5.0 Firefox/130.0'})
    with urllib.request.urlopen(req) as data:
        report = json.load(data)
        upstream_state = {str(item['id']): item for item in report}

    out_of_date = 0
    up_to_date = 0
    skipped = 0
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
            continue  # we only check ST files
        file_id = m.group(1)
        if file_id not in upstream_state:
            skipped += 1  # not updated since_days
            continue

        subfile_id = m.group(2)  # possibly None
        subfiles = upstream_state[file_id].get('files', [])
        if subfile_id is None:
            if len(subfiles) != 1:
                errors += 1
                print(f"{doc.get('assetId')}:")
                print(f"  url must include subfile ID `r=#` as there are {len(subfiles)} subfiles:")
                print("    " + "\n    ".join(f"{r.get('id')}: {r.get('name')}" for r in subfiles))
                print(f"  {upstream_state[file_id].get('fileURL')}")
        else:
            if subfile_id not in [str(r.get('id')) for r in subfiles]:
                errors += 1
                print(f"{doc.get('assetId')}:")
                print(f"  url subfile ID {subfile_id} does not exist (anymore), so must be updated:")
                print("    " + "\n    ".join(f"{r.get('id')}: {r.get('name')}" for r in subfiles))
                print(f"  {upstream_state[file_id].get('fileURL')}")

        last_modified_upstream = isoparse(upstream_state[file_id]['updated'])
        if last_modified_upstream.tzinfo is None:
            last_modified_upstream = last_modified_upstream.replace(tzinfo=timezone.utc)

        if 'lastModified' not in doc:
            errors += 1  # TODO
        else:
            last_modified = isoparse(doc.get('lastModified'))
            # we ignore small timestamp differences
            if abs(last_modified_upstream - last_modified) <= timedelta(minutes=10):
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
                print(f"  {upstream_state[file_id].get('fileURL')}")
                print(f"  {p}")

    skipped_msg = (
            "" if not skipped else
            f" (skipped {skipped} assets not updated in the last {since_days} days)" if not id_mode else
            f" (skipped {skipped} assets)")
    result = 0
    if out_of_date == 0:
        print(f"All {up_to_date} ST assets are up-to-date{skipped_msg}.")
    else:
        print(f"There are {out_of_date} outdated ST assets, while {up_to_date} are up-to-date{skipped_msg}.")
        result |= 0x02
    if errors > 0:
        print(f"Finished with {errors} errors.")
        result |= 0x01
    return result


if __name__ == '__main__':
    sys.exit(main())
