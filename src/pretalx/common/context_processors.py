import sys
import warnings

from django.conf import settings
from django.http import Http404
from django.urls import resolve
from django.utils import translation
from django.utils.formats import get_format
from django_scopes import get_scope

from pretalx.cfp.signals import footer_link, html_head
from pretalx.common.models.settings import GlobalSettings
from pretalx.common.text.phrases import phrases
from pretalx.orga.utils.i18n import get_javascript_format, get_moment_locale


def add_events(request):
    if (
        request.resolver_match
        and set(request.resolver_match.namespaces) & {"orga", "plugins"}
        and not request.user.is_anonymous
    ):
        try:
            url = resolve(request.path_info)
            url_name = url.url_name
            url_namespace = url.namespace
        except Http404:  # pragma: no cover
            url_name = ""
            url_namespace = ""
        return {"url_name": url_name, "url_namespace": url_namespace}
    return {}


def get_day_month_date_format():
    return get_format("SHORT_DATE_FORMAT", use_l10n=True).strip("Y").strip(".-/,")


def locale_context(request):
    context = {
        "js_date_format": get_javascript_format("DATE_INPUT_FORMATS"),
        "js_datetime_format": get_javascript_format("DATETIME_INPUT_FORMATS"),
        "js_locale": get_moment_locale(),
        "quotation_open": phrases.base.quotation_open,
        "quotation_close": phrases.base.quotation_close,
        "DAY_MONTH_DATE_FORMAT": get_day_month_date_format(),
        "rtl": getattr(request, "LANGUAGE_CODE", "en") in settings.LANGUAGES_BIDI,
    }

    lang = translation.get_language()
    context["html_locale"] = translation.get_language_info(lang).get(
        "public_code", lang
    )
    return context


def messages(request):
    return {"phrases": phrases}


def system_information(request):
    context = {}
    _footer = []
    _head = []
    event = getattr(request, "event", None)

    if not request.path.startswith("/orga/"):
        context["footer_links"] = []
        context["header_links"] = []

        if event and get_scope():
            context["footer_links"] = [
                {"label": link.label, "url": link.url}
                for link in event.extra_links.all()
                if link.role == "footer"
            ]
            context["header_links"] = [
                {"label": link.label, "url": link.url}
                for link in event.extra_links.all()
                if link.role == "header"
            ]
        for __, response in footer_link.send(event, request=request):
            if isinstance(response, list):
                _footer += response
            else:  # pragma: no cover
                _footer.append(response)
                warnings.warn(
                    "Please return a list in your footer_link signal receiver, not a dictionary.",
                    DeprecationWarning,
                )
        context["footer_links"] += _footer

        if event and get_scope():
            for _receiver, response in html_head.send(event, request=request):
                _head.append(response)
            context["html_head"] = "".join(_head)

    if settings.DEBUG:
        context["development_mode"] = True
        context["pretalx_version"] = settings.PRETALX_VERSION

    context["warning_update_available"] = False
    context["warning_update_check_active"] = False
    if (
        not request.user.is_anonymous
        and request.user.is_administrator
        and request.path.startswith("/orga")
    ):
        gs = GlobalSettings()
        if gs.settings.update_check_result_warning:
            context["warning_update_available"] = True
        if not gs.settings.update_check_ack and "runserver" not in sys.argv:
            context["warning_update_check_active"] = True
    return context
