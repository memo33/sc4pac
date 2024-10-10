#!/usr/bin/env python3
#
# Checks whether any assets on STEX are newer than stated in our yaml files,
# considering the last 180 days.
# The STEX_API_KEY environment variable must be set for authentication.
#
# Pass directories or yaml files as arguments.

import yaml
import sys
import os
import re
from dateutil.parser import isoparse
from datetime import timezone, timedelta
import urllib.request
import json

stex_api_key = os.environ.get('STEX_API_KEY')  # issued by ST admins
url_id_pattern = re.compile(r".*simtropolis.com/files/file/(\d+)-.*")
since_days = 180


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Pass at least one directory or yaml file to validate as argument.")
        return 1
    if not stex_api_key:
        print("The STEX_API_KEY environment variable must be set for authentication.")
        return 1

    req_url = f"https://community.simtropolis.com/stex/files-api.php?key={stex_api_key}&days={since_days}&mode=updated&sc4only=true&sort=desc"
    req = urllib.request.Request(req_url, headers={'User-Agent': 'Mozilla/5.0 Firefox/130.0'})
    with urllib.request.urlopen(req) as data:
        report = json.load(data)
        upstream_state = {str(item['id']): item for item in report}

    errors = 0
    out_of_date = 0
    up_to_date = 0
    skipped = 0
    for d in args:
        for (root, dirs, files) in os.walk(d):
            for fname in files:
                if not fname.endswith(".yaml"):
                    continue
                p = os.path.join(root, fname)
                with open(p) as f:
                    text = f.read()
                    try:
                        for doc in yaml.safe_load_all(text):
                            if doc is None:  # empty yaml file or document
                                continue

                            # check URLs
                            url = doc.get('url')
                            if url is None:
                                continue  # not an asset
                            m = url_id_pattern.fullmatch(url)
                            if not m:
                                continue  # we only check ST files
                            file_id = m.group(1)
                            if file_id not in upstream_state:
                                skipped += 1  # not updated since_days
                                continue

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

                    except yaml.parser.ParserError:
                        errors += 1

    result = 0
    if out_of_date == 0:
        print(f"All {up_to_date} ST assets are up-to-date (skipped {skipped} assets not updated in the last {since_days} days).")
    else:
        print(f"There are {out_of_date} outdated ST assets, while {up_to_date} are up-to-date (skipped {skipped} assets not updated in the last {since_days} days).")
        result |= 0x02
    if errors > 0:
        print(f"Finished with {errors} errors.")
        result |= 0x01
    return result


if __name__ == '__main__':
    sys.exit(main())
