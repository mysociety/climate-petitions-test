#!/usr/bin/env python3
"""
Import petitions data from petitions.parliament.uk
"""

import json
from collections import defaultdict
from time import sleep
from urllib.parse import parse_qs, urlparse

import requests
from sqlite_utils import Database


def main():
    keywords = []

    try:
        with open("keywords.csv") as f:
            keywords = [l.strip() for l in f]
    except FileNotFoundError:
        print("Error: keywords.csv file not found. Aborting.")
        return 1

    print(
        "Loaded {} keywords from keywords.csv: {}".format(
            len(keywords), ", ".join(keywords)
        )
    )

    db = Database("data.sqlite")

    for keyword in keywords:
        next_page = 1
        while next_page > 0:
            r = requests.get(
                "https://petition.parliament.uk/petitions.json",
                params={"q": keyword, "page": next_page},
            )

            assert r.status_code == 200, "{} returned status code {}".format(
                r.url, r.status_code
            )

            print(r.url)

            j = r.json()

            for p in j["data"]:
                petition = extract_petition_data(p)

                db["petitions"].upsert(petition, pk="id").m2m(
                    "keywords", lookup={"keyword": keyword}
                )

            if j["links"]["next"]:
                next_page = get_page_number_from_url(j["links"]["next"])
            else:
                next_page = 0

            sleep(1)

    large_petitions = db.query("select * from petitions where signature_count >= 10000")

    for petition in large_petitions:
        print(petition["url"])
        r = requests.get(petition["url"])
        if r.status_code != 200:
            print(f"failed to fetch {petition['url']}: {r.status_code}")
            continue

        j = r.json()
        for cons in j["data"]["attributes"]["signatures_by_constituency"]:
            sigs = {
                "petition_id": petition["id"],
                "constituency": cons["name"],
                "gss": cons["ons_code"],
                "signatures": cons["signature_count"],
            }

            db["constituency_signatures"].upsert(
                sigs,
                pk=("gss", "petition_id"),
                foreign_keys=[("petition_id", "petitions", "id")],
            )

        sleep(1)

    cons = db.query("select distinct(gss) from constituency_signatures")

    top_petitions = defaultdict(list)
    for con in cons:
        petitions = db.query(
            "select petitions.*, constituency_signatures.* from petitions, constituency_signatures where constituency_signatures.petition_id = petitions.id and gss = ? order by signatures desc limit 3",
            [con["gss"]],
        )
        for petition in petitions:
            top_petitions[con["gss"]].append(petition)

    with open("top_three_per_cons.json", "w") as output:
        json.dump(top_petitions, output)


def extract_petition_data(p):
    petition = {
        "id": p["id"],
        "url": p["links"]["self"],
        "state": p["attributes"]["state"],
        "action": p["attributes"]["action"],
        "background": p["attributes"]["background"],
        "additional_details": p["attributes"]["additional_details"],
        "signature_count": p["attributes"]["signature_count"],
        "date_created": p["attributes"]["created_at"],
    }

    try:
        petition["date_responded"] = p["attributes"]["government_response"][
            "responded_on"
        ]
    except TypeError:
        petition["date_responded"] = None

    try:
        petition["date_debated"] = p["attributes"]["debate"]["debated_on"]
    except TypeError:
        petition["date_debated"] = None

    return petition


def get_page_number_from_url(url):
    u = urlparse(url)
    q = parse_qs(u.query)
    return int(q["page"][0])


if __name__ == "__main__":
    main()
