# pip install --upgrade google-api-python-client

import os
from googleapiclient.discovery import build
from subprocess import check_output

service = build("customsearch", "v1", developerKey=os.getenv("GOOGLE_API_KEY"))

IGNORE_ARXIV_CODES = [
    # Known false positives.
    "1311.0759",
    "1609.05401",
    "1612.02010"    
]

formatted_urls = []

kwds = dict(cx=os.getenv("GOOGLE_SEARCH_API_CX"),
            q="\"Gaia Sprint\" filetype:pdf",
            num=10)

results = service.cse().list(**kwds).execute()

for item in results["items"]:
    formatted_urls.append(item["formattedUrl"])

N = int(results["queries"]["request"][0]["totalResults"])

while True:
    results = service.cse().list(
        start=results["queries"]["nextPage"][0]["startIndex"],
        **kwds).execute()

    for item in results["items"]:
        formatted_urls.append(item["formattedUrl"])

    if not "nextPage" in results["queries"]:
        break

print("Found {} urls".format(len(formatted_urls)))
missing = []
for formatted_url in formatted_urls:

    arxiv_code = formatted_url.split("/")[-1]
    if arxiv_code in IGNORE_ARXIV_CODES:
        print("Skipping {}".format(arxiv_code))
        continue

    print("Checking {}".format(formatted_url))

    try:
        output = check_output(["grep", arxiv_code, "-r", "."])

    except:
        missing.append(formatted_url)

for each in missing:
    print("Could not find reference to {}".format(each))

print("Fin.")