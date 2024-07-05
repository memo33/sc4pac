#!/usr/bin/env python3
#
# Checks whether any assets on SC4E are newer than stated in our yaml files.
#
# Pass directories or yaml files as arguments.

import yaml
import sys
import os
import re
from dateutil.parser import isoparse
from datetime import timezone
import urllib.request
import json

sc4eUrlIdPattern = re.compile(r".*sc4evermore.com/.*[?&]id=(\d+):.*")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        "Pass at least one directory or yaml file to validate as argument."
        return 1

    req = urllib.request.Request("https://www.sc4evermore.com/latest-modified-downloads.php", headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as data:
        report = json.load(data)
        upstreamState = {item['id']: item for item in report['files']}

    errors = 0
    outOfDate = 0
    upToDate = 0
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
                            m = sc4eUrlIdPattern.fullmatch(url)
                            if not m:
                                continue  # we only heck SC4E files
                            fileId = m.group(1)

                            lastModifiedUpstream = isoparse(upstreamState[fileId]['modified'])
                            if lastModifiedUpstream.tzinfo is None:
                                lastModifiedUpstream = lastModifiedUpstream.replace(tzinfo=timezone.utc)

                            if 'lastModified' not in doc:
                                errors += 1  # TODO
                            else:
                                lastModified = isoparse(doc.get('lastModified'))
                                if lastModified == lastModifiedUpstream:
                                    upToDate += 1
                                else:
                                    if lastModified < lastModifiedUpstream:
                                        outOfDate += 1
                                    else:
                                        errors += 1  # our assets should not be newer than upstream's assets TODO
                                        print("error: ", end='')
                                    print(f"{doc.get('assetId')}:")
                                    print(f"  {doc.get('version')} -> {upstreamState[fileId].get('release')}")
                                    print(f"  {lastModified.isoformat().replace('+00:00', 'Z')} -> {lastModifiedUpstream.isoformat().replace('+00:00', 'Z')}")
                                    print(f"  https://www.sc4evermore.com/index.php/downloads/download/{fileId}")
                                    print(f"  {p}")

                    except yaml.parser.ParserError:
                        errors += 1

    result = 0
    if outOfDate == 0:
        print(f"All {upToDate} SC4E assets are up-to-date.")
    else:
        print(f"There are {outOfDate} outdated SC4E assets, while {upToDate} are up-to-date.")
        result |= 0x02
    if errors > 0:
        print(f"Finished with {errors} errors.")
        result |= 0x01
    return result


if __name__ == '__main__':
    sys.exit(main())
