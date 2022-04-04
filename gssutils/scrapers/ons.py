from csv import DictReader
from io import StringIO
import logging
import mimetypes
import os
from urllib.parse import urlparse, urlunparse

import backoff
from dateutil import tz
from dateutil.parser import parse, isoparse, ParserError
from distutils.util import strtobool

from gssutils.metadata.dcat import Distribution
from gssutils.metadata.mimetype import Excel, ODS, CSV, ExcelOpenXML, CSDB


# save ourselves some typing later
ONS_PREFIX = "https://www.ons.gov.uk"
ONS_DOWNLOAD_PREFIX = ONS_PREFIX + "/file?uri="
ONS_TOPICS_CSV = 'https://gss-cogs.github.io/ref_common/reference/codelists/ons-topics.csv'


def get_dict_from_json_url(url, scraper):
    """ Wrapper to Let the DE decide if they want retries or not via an env var"""
    if strtobool(os.getenv("ONS_SCRAPER_RETRIES", "False")):
        return retry_get(url, scraper)
    return get(url, scraper)


def get(url, scraper):
    """ Given a url, return a dict"""
    r = scraper.session.get(url)
    if not r.ok:
        raise ValueError(f"Aborting. Issue encountered while attempting to scrape '{url}'. Http code"
                        f" returned was '{r.status_code}.")
    return r.json()


@backoff.on_exception(backoff.expo, Exception, max_time=30)
def retry_get(url, scraper):
    """ Given a url, return a dict, with retries for errors"""
    try:
        return get(url, scraper)
    except Exception as err:
        print(f'Retrying failed attempt to get dict from json. Error was: {err}')
        raise err

    
def scrape(scraper, tree):
    """
    This is json scraper for ons.gov.uk pages
    This scraper will attempt to gather metadata from "standard" fields shared across page types
    then drop into page-type specific handlers.
    :param scraper:         the Scraper object
    :param landing_page:    the provided url
    :return:
    """

    landing_page = get_dict_from_json_url(scraper.uri + "/data", scraper)

    accepted_page_types = ["dataset_landing_page", "static_adhoc"]
    if landing_page["type"] not in accepted_page_types:
        raise ValueError("Aborting operation This page type is not supported.")

    scraper.dataset.title = landing_page["description"]["title"].strip()

    scraper.dataset.issued = parse_as_local_date(landing_page["description"]["releaseDate"])

    # TODO, depends on outcome of https://github.com/GSS-Cogs/gss-utils/issues/308
    page_type = landing_page["type"]
    if page_type == "dataset_landing_page":
        scraper.dataset.comment = landing_page["description"]["summary"].strip()
        scraper.dataset.description = landing_page["description"]["metaDescription"]
    else:
        scraper.dataset.comment = landing_page["markdown"][0].split("\n")[0].strip()
        scraper.dataset.description = landing_page["markdown"][0]

    try:
        # Account for people replacing an expected date field with free text, eg: "this is discontinued".
        # Warn user (in case that's not the issue) but allow the scrape to continue.
        # Note: I dislike how broad this is but the ONS is wildly inconsistent in the notice text they're using,
        # so we're just gonna have to throw a wanring at the DE's and let them make an informed choice
        # where this occurs.
        try:
            scraper.dataset.updateDueOn = parse(landing_page["description"]["nextRelease"], dayfirst=True)
        except ParserError as err:
            logging.warning(
                f'Unable to parse ["description"]["nextRelease"] nextRelease field from: {scraper.uri + "/data"}.'
                f' with date ParseError of: "{err}". Continuing scrape without this data.')

    except KeyError:
        logging.debug("no description.nextRelease key in json, skipping")

    try:
        contact_dict = landing_page["description"]["contact"]
        scraper.dataset.contactPoint = "mailto:" + contact_dict["email"].strip()
    except KeyError:
        logging.debug("no description.contact key in json, skipping")

    scraper.dataset.keyword = list(
        set([x.strip() for x in landing_page["description"]["keywords"]]))

    scraper.dataset.publisher = 'https://www.gov.uk/government/organisations/office-for-national-statistics'
    scraper.dataset.license = "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"

    topics_response = scraper.session.get(
        ONS_TOPICS_CSV,
        stream=True
    )
    topics_reader = DictReader(StringIO(topics_response.content.decode('utf-8')))
    prefix = None
    parsed_uri = urlparse(scraper.uri)
    for row in topics_reader:
        if parsed_uri.path.startswith(row['Path']):
            if prefix is None or len(prefix) < len(row['Path']):
                prefix = row['Path']

    scraper.dataset.theme = urlunparse(parsed_uri._replace(path=prefix))

    # From this point the json structure vary based on the page type
    # so we're switching to page-type specific handling
    page_handlers = {
        "static_adhoc": handler_static_adhoc,
        "dataset_landing_page": handler_dataset_landing_page
    }

    # if the page "type" isn't one we do, blow up
    if page_type not in page_handlers.keys():
        raise ValueError("Aborting operation. Scraper cannot handle page of type '{}'.".format(page_type))

    page_handlers[page_type](scraper, landing_page, tree)


def parse_as_local_date(dt: str):
    """
    Dates provided by the /data JSON are actually given as date times using ISO 8601 with UTC, so during
    British Summer Time, will be one hour before midnight the day before.
    We can account for this if we figure out the datetime in the Europe/London timezone and then take the date.
    """
    tz_ons = tz.gettz('Europe/London')
    return isoparse(dt).astimezone(tz_ons).date()


def handler_dataset_landing_page_fallback(scraper, this_dataset_page, tree):
    """
    At time of writing there's an issue with the latest version of datasets 404'ing on the
    versions page.
    
    this function will create what the latest version should be, using the information on the
    base dataset landing page.
    """

    logging.warning("Using fallback logic to scrape latest distribution from dataset landing page (rather "
                    "than previous page). This scrape will only have a single distribution of xls.")

    this_distribution = Distribution(scraper)

    release_date = this_dataset_page["description"]["releaseDate"]
    this_distribution.issued = parse(release_date.strip()).date()

    # gonna have to go via html ...
    download_url = tree.xpath("//a[text()='xls']/@href")
    this_distribution.downloadURL = download_url

    media_type = media_type, _ = mimetypes.guess_type(download_url)
    this_distribution.mediaType = media_type

    this_distribution.title = scraper.dataset.title
    this_distribution.description = scraper.dataset.description
    this_distribution.contactPoint = scraper.dataset.contactPoint

    logging.debug("Created distribution for download '{}'.".format(download_url))
    scraper.distributions.append(this_distribution)


def handler_dataset_landing_page(scraper, landing_page, tree):
    # A dataset landing page has uri's to one or more datasets via it's "datasets" field.
    # We need to look at each in turn, this is an example one as json:
    # https://www.ons.gov.uk//businessindustryandtrade/internationaltrade/datasets/uktradeingoodsbyclassificationofproductbyactivity/current/data
    for dataset_page_url in landing_page["datasets"]:

        this_dataset_page = get_dict_from_json_url(ONS_PREFIX + dataset_page_url["uri"] + "/data", scraper)

        # create a list, with each entry a dict of a versions url and update date
        versions_dict_list = []

        # Where the dataset is versioned, use the versions as the distributions
        try:
            all_versions = this_dataset_page["versions"]
        except KeyError:
            all_versions = []

        # Release dates:
        # --------------
        # ONS does this odd thing where each version on the /data api
        # has a updateDate field which is actually the date THE DATA
        # WAS SUPERCEDED (so the release fate of the NEXT version of the data).
        # ......this takes a bit of unpicking.

        # If no initial release date for the dataset has been provided
        # We're just going to ignore v1, we don't have a use for it
        # and with no provided release date ... not a lot to be done
        initial_release = this_dataset_page["description"].get("releaseDate", None)

        next_release = None
        # Where there's multiple versions, iterate all and populate a list
        if len(all_versions) != 0:
            try:
                for version_as_dict in all_versions:
                    if next_release is None:
                        release_date = initial_release
                    else:
                        release_date = next_release

                    if release_date is not None:
                        versions_dict_list.append({
                            "url": ONS_PREFIX + version_as_dict["uri"] + "/data",
                            "issued": release_date
                        })
                    next_release = version_as_dict["updateDate"]
            except KeyError:
                logging.debug("No older versions found for {}.".format(dataset_page_url))

        # Add the current release
        versions_dict_list.append({
            "url": ONS_PREFIX + this_dataset_page["uri"] + "/data",
            "issued": initial_release if next_release is None else next_release
        })

        # NOTE - we've had an issue with the very latest dataset not being updated on the previous versions
        # page (the page we're getting the distributions from) so we're taking the details for it from
        # the landing page to use as a fallback in that scenario.

        # iterate through the lot, we're aiming to create at least one distribution object for each
        for i, version_dict in enumerate(versions_dict_list):

            version_url = version_dict["url"]
            issued = version_dict["issued"]

            logging.debug("Identified distribution url, building distribution object for: " + version_url)

            # get the response json into a python dict
            this_page = get_dict_from_json_url(version_url, scraper)

            # Get the download urls, if there's more than 1 format of this version of the dataset
            # each forms a separate distribution
            distribution_formats = this_page["downloads"]
            for dl in distribution_formats:

                # Create an empty Distribution object to represent this distribution
                # from here we're just looking to fill in it's fields
                this_distribution = Distribution(scraper)
                this_distribution.issued = parse_as_local_date(issued)

                # I don't trust dicts with one constant field (they don't make sense), so just in case...
                try:
                    download_url = ONS_DOWNLOAD_PREFIX + this_page["uri"] + "/" + dl["file"].strip()
                    this_distribution.downloadURL = download_url
                except:
                    # Throw a warning and abandon this distribution, ff we don't have a downloadURL it's not much use
                    logging.warning("Unable to create complete download url for {} on page {}"
                                    .format(dl, version_url))
                    continue

                # we've had some issues with type-guessing so we're getting the media type
                # by checking the download url ending
                if download_url.endswith(".csdb"):
                    media_type = CSDB
                else:
                    media_type, _ = mimetypes.guess_type(download_url)

                this_distribution.mediaType = media_type
                
                # inherit metadata from the dataset where it hasn't explicitly been changed
                this_distribution.title = scraper.dataset.title
                this_distribution.description = scraper.dataset.description

                logging.debug("Created distribution for download '{}'.".format(download_url))
                scraper.distributions.append(this_distribution)


def handler_static_adhoc(scraper, landing_page, tree):
    # A static adhoc is a one-off unscheduled release
    # These pages should be simpler and should lack the historical distributions

    for download in landing_page["downloads"]:

        title = download["title"]
        file = download["file"]

        # Create an empty Distribution object to represent this distribution
        # from here we're just looking to fill in it's fields
        this_distribution = Distribution(scraper)

        # if we can't get the release date, continue but throw a warning.
        try:
            this_distribution.issued = parse(landing_page["description"]["releaseDate"]).date()
        except KeyError:
            logging.warning("Unable to acquire or parse release date")

        download_url = ONS_DOWNLOAD_PREFIX + landing_page["uri"] + "/" + file
        this_distribution.downloadURL = download_url

        # TODO - we're doing this in two place, pull it out
        # we've had some issues with type-guessing so we're getting the media type
        # by checking the download url ending
        if download_url.endswith(".csdb"):
            media_type = CSDB
        else:
            media_type, _ = mimetypes.guess_type(download_url)

        this_distribution.mediaType = media_type

        this_distribution.title = title

        # inherit metadata from the dataset where it hasn't explicitly been changed
        this_distribution.description = scraper.dataset.description

        logging.debug("Created distribution for download '{}'.".format(download_url))
        scraper.distributions.append(this_distribution)