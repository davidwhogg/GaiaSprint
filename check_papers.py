# pip install --upgrade google-api-python-client

import os

import ads
from googleapiclient.discovery import build
from subprocess import check_output
from glob import glob

service = build("customsearch", "v1", developerKey=os.getenv("GOOGLE_API_KEY"))

IGNORE_ARXIV_CODES = [
    # Known false positives.
    "1311.0759",
    "1609.05401",
    "1612.02010",
    "1811.03919"
]

# Already added these.
IGNORE_ADS_ARTICLE_IDS = [
    15118334,
    15714195,
    15612118
]
# check and add these 
CHECK_ARXIV_CODES = [
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

if len(CHECK_ARXIV_CODES) > 0:
    for each in CHECK_ARXIV_CODES:
        url = f"https://arxiv.org/pdf/{each}"

        if url not in formatted_urls:
            formatted_urls.append(url)


files = glob("*.html")
missing = []
for formatted_url in formatted_urls:

    arxiv_code = formatted_url.split("/")[-1]
    if arxiv_code in IGNORE_ARXIV_CODES:
        print("Skipping {}".format(arxiv_code))
        continue

    print("Checking {}".format(formatted_url))

    command = ["grep", arxiv_code]
    command.extend(files)
    try:
        output = check_output(command)

    except:
        missing.append(formatted_url)

for each in missing:
    print("Could not find reference to {}".format(each))


match_acks = [
    ("2019 Santa Barbara Gaia Sprint", "2019SB.html"),
    ("2018 NYC Gaia Sprint", "2018NYC.html"),
    ("2017 Heidelberg Gaia Sprint", "2017HD.html"),
    ("2016 NYC Gaia Sprint", "2016NYC.html"),
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


# Search for articles using ADS full text search and acknowledgement search.
for ack, page in match_acks:
    results = list(ads.SearchQuery(q=f"ack:\"{ack}\"", fl=["identifier", "title", "author"]))

    for article in results:

        if int(article.id) in IGNORE_ADS_ARTICLE_IDS:
            continue

        for identifier in article.identifier:
            if "arxiv:" in identifier.lower():
                arxiv_code = identifier.split(":")[1]
                break
        else:
            print(f"Warning: cannot find arXiv identifier to http://adsabs.harvard.edu/abs/{article.identifier[0]} (article id {article.id})")
            continue

        if arxiv_code in IGNORE_ARXIV_CODES:
            continue

        command = ["grep", arxiv_code]
        command.append(page)
        try:
            output = check_output(command)

        except:
            # It's new.
            title = article.title[0]
            num_authors = len(article.author)
            if num_authors == 1:
                authors = article.author[0]
            elif num_authors < 10:
                authors = ", ".join(article.author[:-1]) + " and " + article.author[-1]
            else:
                authors = "{0} et al.".format(article.author[0])

            new_content = f"    <li><a href=\"https://arxiv.org/abs/{arxiv_code}\">{title}</a>, {authors}</li>\n"

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

