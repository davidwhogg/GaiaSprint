# pip install --upgrade google-api-python-client

import os

import ads
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


match_acks = [
    ("2018 NYC Gaia Sprint", "2018NYC.html"),
    ("2017 Heidelberg Gaia Sprint", "2017HD.html"),
    ("2016 NYC Gaia Sprint", "2016NYC.html")
]


# Search for each missing item.
for each in missing:

    arxiv_code = each.split("/")[-1]
    results = list(ads.SearchQuery(q=f"identifier:\"{arxiv_code}\""))

    # Find out which sprint it was.
    assert len(results) > 0
    for ack, page in match_acks:
        r = list(ads.SearchQuery(q=f"identifier:\"{arxiv_code}\" AND ack:\"({ack})\""))
        if len(r) > 0:
            break

    else:
        page = None


    for article in results:
        title = article.title[0]
        num_authors = len(article.author)
        if num_authors == 1:
            authors = article.author[0]
        elif num_authors < 10:
            authors = ", ".join(article.author[:-1]) + " and " + article.author[-1]
        else:
            authors = "{0} et al.".format(article.author[0])

        new_content = f"    <li><a href=\"https://arxiv.org/abs/{arxiv_code}\">{title}</a>, {authors}</li>\n"

        break

    if page is None:
        page = match_acks[0][-1]

        print(f"Warning: auto-assigning to {page}:\n{new_content}")


    print(f"PAGE: {page}")
    print(new_content)

    with open(page, "r") as fp:
        # Find first <ul>
        content = fp.read()

    search_string = "<ul>\n"
    pos = content.index(search_string) + len(search_string)

    updated_content = content[:pos] + new_content + content[pos:]

    with open(page, "w") as fp:
        fp.write(updated_content)

    os.system(f"git add {page}")
    os.system(f"git commit -m \"auto-commit paper {arxiv_code}\"")

