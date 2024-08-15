
from newsapi import NewsApiClient
import psycopg2
import sys
import requests
from config import load_config
import argparse
# Load configuration and connect to the database
config = load_config()
conn = psycopg2.connect(**config)
cursor = conn.cursor()



from transformers import pipeline

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def summarize_article(article, chunk_size=512):
    article_length = len(article.split())
    chunks = [article[i:i + chunk_size] for i in range(0, article_length, chunk_size)]
    summaries = [summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text'] for chunk in chunks]
    return " ".join(summaries)

ARTICLE ="""LOS ANGELES (KABC) -- Homelessness in the city of Los Angeles is down for the first time in six years, and this year is the first time the city has seen a double-digit decrease in street homelessness in nearly a decade.

The Los Angeles Homeless Services Authority, a joint powers agency of the city and county of L.A., announced the numbers from the Greater Los Angeles Homeless Count during a Friday morning news conference, detailing data that was gathered during an annual point-in-time survey conducted by hundreds of volunteers all across the region from Jan. 24- 26.

Top results from 2024 homeless count for city of Los Angeles
Homelessness in L.A. is down for the first time in six years. There were 45,252 unhoused individuals in the city in 2024 compared to 46,260 in 2023, a drop of 2.2%
symbol



Unsheltered homelessness decreased by approximately 10.7% - that's the first double-digit decrease in at least nine years, according to the city.
38% decrease in makeshift shelters
Shelter count increased by 17.7%

"For so many years, the count has shown increases in homelessness, and we have all felt that in our neighborhoods. But we leaned into change. And we have changed the trajectory of this crisis and have moved L.A. in a new direction," said Mayor Karen Bass in a statement. "There is nothing we cannot do by taking on the status quo, putting politics aside, and rolling up our sleeves to work together. I want to thank the City Council, the County Board of Supervisors, LAHSA, our state, federal and community partners and our service provider partners for locking arms to confront this crisis with the urgency that it requires. This is not the end, it is the beginning - and we will build on this progress, together."

What about homelessness in L.A. County?
According to the report, there were 75,312 unhoused people in the county in 2024 compared to 75,518 in 2023, a dip of 0.27%;

There was also a reduction in unsheltered homelessness in L.A. County, with a 5.1% decrease compared to last year, while the shelter count increased by 12.7%.

Officials attributed the downward trends to "unprecedented policy alignment and investments" made by the city, county, state and federal governments, according to Paul Rubenstein, LAHSA deputy chief of external relations.

With more unhoused individuals entering shelter or other forms of temporary housing, Rubenstein said, officials are "cautiously optimistic about the direction of homelessness across L.A. County" and are in a position to move more people off the streets and into permanent housing.


L.A. County Supervisor Janice Hahn, meanwhile, released a statement saying, "For the first time in years, the number of people sleeping on our streets is down and the number of people in our shelters is up. We have focused on shelters and we are doing a better job convincing people to come inside. The next step is building more permanent supportive housing and investing in long- term solutions to this crisis."

The count also noted a reduction in chronic homelessness in the L.A. Continuum of Care, covering most of L.A. County except the cities of Long Beach, Pasadena and Glendale. There were 6.8% fewer people experiencing chronic homelessness -- a term used to describe individuals who have been homeless for more than a year while struggling with a disabling condition -- compared to 2023, the report said. Of those, some 9.4% were unsheltered while 7.5% more were in shelters.

"Our coordinated efforts are moving the needle and we have to stick together in addition to moving people into interim housing," Rubenstein said. "The rehousing system also gained significant momentum this year. We made a breaking 28,000 permanent housing placements."

He added, "At this rate, if we could stop anyone else from becoming homeless today, we could end homelessness in just a few years."

In addition, the 2024 count showed family homelessness increased by 2.2%, though many families are in temporary housing. Among transition-age youth -- individuals coming out of the foster system between the ages of 16-24 -- homelessness decreased by 16.2% and veteran homelessness decreased by 22.9%.


LAHSA reported that about 22% of unhoused individuals report experiencing serious mental illness, while another 24% of unhoused individuals report experiencing substance use disorder -- both figures decreased compared to 2023 and 2022.

Following the results of the 2023 Homeless Count, L.A county and city officials committed to a collaborative approach to reducing homelessness and bringing unhoused individuals into temporary and permanent housing.

In December 2022, Bass launched her Inside Safe initiative in an effort to reduce tents and other encampments across city streets and bring unhoused individuals into temporary housing. Bass and the L.A. City Council have also implemented programs aimed at bolstering housing production, increasing shelter beds and sustaining tiny home villages, interim housing sites and other housing facilities with the intent of placing unhoused individuals into permanent housing.

County officials launched a similar program to that of Inside Safe, known as Pathway Home, in 2023.

LASHA officials noted that Measure HHH -- a $1.2 billion bond measure approved by L.A. voters in 2016 -- has played a significant role in building supportive and affordable housing, which in part led to the results seen in the 2024 Homeless Count.

City News Service, Inc. contributed to this report."""

print(summarize_article(ARTICLE))
