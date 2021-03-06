import re
import cgi
import urllib
import jinja2
from jingo import register

from django.template import Context
from django.template.loader import get_template
from django.conf import settings
from django.utils.timesince import timesince as _timesince

from bootstrapform.templatetags.bootstrap import bootstrap_horizontal

from airmozilla.main.models import Event, EventOldSlug
from airmozilla.comments.models import Comment


@register.function
def bootstrapform(form):
    template = get_template("bootstrapform/form.html")
    context = Context({'form': form})
    return template.render(context)


@register.function
def bootstrapform_horizontal(form):
    return bootstrap_horizontal(form, 'col-sm-3 col-lg-3')


@register.function
def invalid_form(form):
    """return true if the form is bound and invalid"""
    return form.is_bound and not form.is_valid()


@register.function
def query_string(request, **kwargs):
    current = request.META.get('QUERY_STRING')
    parsed = cgi.parse_qs(current)
    parsed.update(kwargs)
    return urllib.urlencode(parsed, True)


@register.function
def clashes_with_event(url):
    """used for URLs belonging to Flatpages to see if their
    URL is possibly clashing with an event.
    """
    possible = url.split('/', 2)[1]
    try:
        return Event.objects.get(slug=possible)
    except Event.DoesNotExist:
        try:
            return EventOldSlug.objects.get(slug=possible).event
        except EventOldSlug.DoesNotExist:
            return False


@register.function
def full_tweet_url(tweet_id):
    return (
        'https://twitter.com/%s/status/%s'
        % (
            settings.TWITTER_USERNAME,
            tweet_id
        )
    )


@register.function
def scrub_transform_passwords(text):
    for password in settings.URL_TRANSFORM_PASSWORDS.values():
        text = text.replace(
            password,
            'XXXpasswordhiddenXXX'
        )
    return text


@register.function
def timesince(start_time):
    return _timesince(start_time)


basic_markdown_link = re.compile(
    '(\[(.*?)\]\((/.*?)\))'
)


@register.function
def format_message(message):
    if hasattr(message, 'message'):
        # it's a django.contrib.messages.base.Message instance
        message = message.message

    if basic_markdown_link.findall(message):
        whole, label, link = basic_markdown_link.findall(message)[0]
        message = message.replace(
            whole,
            '<a href="%s" class="message-inline">%s</a>'
            % (link, label)
        )
        message = jinja2.Markup(message)

    return message


@register.function
def almost_equal(date1, date2):
    """return true if the only difference between these two dates are
    their microseconds."""
    diff = abs(date1 - date2)
    return not diff.seconds and not diff.days


@register.function
def comment_status_to_css_label(status):
    # because this just got too messy in the template
    if status == Comment.STATUS_APPROVED:
        return 'label-success'
    elif status == Comment.STATUS_REMOVED:
        return 'label-danger'
    return 'label-info'
