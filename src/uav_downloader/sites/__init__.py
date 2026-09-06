"""Site registry for featured and compatibility-only URL adapters."""

from __future__ import annotations

import os

from . import hanime1, jabletv, missav, supjav
from .legacy import sites_91porn, sites_javdb
from uav_downloader.core import config
from uav_downloader.core.urls_watch import iter_url_batches
from uav_downloader.i18n.locales import T, set_lang


FEATURED_SITE_CLASSES = (
    jabletv.SiteJableTV,
    jabletv.SiteJableTV_Backup,
    missav.SiteMissAV,
    supjav.SiteSupJav,
    hanime1.SiteHanime1,
)

LEGACY_URL_ONLY_SITE_CLASSES = (
    sites_91porn.SiteJableOrg,
    sites_91porn.SiteThisAV,
    sites_91porn.SitePigAV,
    sites_91porn.SitePorn5F,
    sites_91porn.Site85Tube,
    sites_91porn.Site91Porn,
    sites_91porn.SitePornBest,
    sites_javdb.SiteJavdbLive,
    sites_javdb.SiteHAnimeXYZ,
    sites_javdb.SitePornTW,
    sites_javdb.SitePornJP,
    sites_javdb.SitePornHK,
    sites_javdb.SitePornHoHo,
    sites_javdb.SitePornNVR,
    sites_javdb.SiteVideo01,
    sites_javdb.SitePornLuLu,
    sites_javdb.SiteMIEN321,
    sites_javdb.SiteAApp11,
    sites_javdb.SiteSeselah,
    sites_javdb.SiteXJISHI,
)

# Backward-compatible public names used throughout the original application.
siteList = FEATURED_SITE_CLASSES + LEGACY_URL_ONLY_SITE_CLASSES
siteUrlList = (jabletv.JableTVList,)


def validate_url(url):
    for site in siteList:
        if site.validate_url(url):
            return site
    return None


def VaildateUrl(url):  # noqa: N802 - legacy API typo retained for v2 callers
    return validate_url(url)


def create_site(url, savepath="", silence=False, max_workers=None,
                 filename_mode=None):
    site = validate_url(url)
    if site is None:
        return None
    kwargs = {}
    if max_workers is not None:
        kwargs['max_workers'] = max_workers
    if filename_mode is not None:
        kwargs['filename_mode'] = filename_mode
    return site(url, savepath=savepath, silence=silence, **kwargs)


def CreateSite(url, savepath="", silence=False, max_workers=None,  # noqa: N802
               filename_mode=None):
    return create_site(url, savepath, silence, max_workers, filename_mode)


def create_site_url_list(url, silence=False):
    for url_list in siteUrlList:
        candidate = url_list(url, silence=silence)
        if candidate.isVaildLinks():
            return candidate
    return None


def CreateSiteUrlList(url, silence=False):  # noqa: N802
    return create_site_url_list(url, silence)


def consoles_main(url, dest=None, max_workers=None, filename_mode=None,
                   watch_urls_file=None):
    set_lang(config.get_ui_lang() or 'en')
    if url:
        url_batches = [[url]]
    elif watch_urls_file:
        urls_path = os.path.join(dest or '.', 'urls.txt')
        url_batches = iter_url_batches(urls_path, watch_urls_file)
    else:
        url_batches = [[input(T('console_input_url_prompt'))]]

    for urls in url_batches:
        for one_url in urls:
            job = create_site(
                one_url, dest, max_workers=max_workers,
                filename_mode=filename_mode)
            if job and job.is_url_vaildate():
                job.start_download()
                print(T('console_job_done'))


if __name__ == "__main__":
    consoles_main("")
