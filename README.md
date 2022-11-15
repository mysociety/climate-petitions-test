# Climate petitions test

An experiment for https://github.com/mysociety/local-intelligence-hub/issues/52.

## Running this locally

Create and activate the Python virtual environment, and install the required packages:

    python3 -m venv venv
    . venv/bin/activate
    pip3 install -r requirements.txt

The import script will retrieve petitions from https://petitions.parliament.uk based on the keywords you provide. List your keywords, one per line, in `keywords.csv`. You can copy the defaults if you like:

    cp default-keywords.csv keywords.csv

Run the import script:

    script/import_petitions.py

Data will be saved to a SQLite file at `data.sqlite`

## Useful SQL queries

Popular (10,000+ signatures) petitions, with the keywords that returned them, sorted by popularity:

    select group_concat(keywords.keyword) as keywords, petitions.* from petitions, keywords, keywords_petitions where keywords_petitions.keywords_id = keywords.id and keywords_petitions.petitions_id = petitions.id and signature_count > 10000 group by petitions.id order by signature_count desc

Number of petitions returned for each keyword:

    select keywords.keyword, count(keywords_petitions.petitions_id) from keywords, keywords_petitions where keywords_petitions.keywords_id = keywords.id group by keywords_petitions.keywords_id

Number of petitions with X number of signatures:

    select signature_count as n_signatures, count(id) as n_petitions from petitions group by signature_count order by signature_count desc

Number of petitions by month:

    select strftime('%Y-%m', petitions.date_created) as month, count(id) as n_petitions from petitions group by month order by month desc

Some stats on responses:

    select count(id) from petitions where date_responded is not null

    select count(id) from petitions where date_debated is not null

