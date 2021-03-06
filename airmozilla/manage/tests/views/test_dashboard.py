import datetime
import json

from nose.tools import eq_, ok_

from django.utils.timezone import utc
from django.contrib.auth.models import User

from funfactory.urlresolvers import reverse

from .base import ManageTestCase


class TestDashboard(ManageTestCase):

    def test_dashboard(self):
        response = self.client.get(reverse('manage:dashboard'))
        eq_(response.status_code, 200)

    def test_dashboard_data(self):

        def user_counts(response):
            data = json.loads(response.content)
            return [
                x['counts'] for x in data['groups'] if x['name'] == 'New Users'
            ][0]

        # we're logged in as user 'fake'
        # delete the others
        User.objects.exclude(username='fake').delete()
        user, = User.objects.all()

        now = datetime.datetime.utcnow().replace(tzinfo=utc)
        # let's pretend this user was created today
        user.date_joined = now
        user.save()

        url = reverse('manage:dashboard_data')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        counts = user_counts(response)
        eq_(counts['today'], 1)
        eq_(counts['today_delta'], 1)  # one more than last yesterday
        eq_(counts['this_week'], 1)
        eq_(counts['this_week_delta'], 1)
        eq_(counts['this_month'], 1)
        eq_(counts['this_month_delta'], 1)
        eq_(counts['this_year'], 1)
        eq_(counts['this_year_delta'], 1)
        eq_(counts['ever'], 1)

        user.date_joined -= datetime.timedelta(days=1)
        user.save()
        url = reverse('manage:dashboard_data')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        counts = user_counts(response)
        eq_(counts['today'], 0)
        eq_(counts['today_delta'], -1)  # one more than yesterday
        eq_(counts['this_week'], 1)
        eq_(counts['this_week_delta'], 1)
        eq_(counts['this_month'], 1)
        eq_(counts['this_month_delta'], 1)
        eq_(counts['this_year'], 1)
        eq_(counts['this_year_delta'], 1)
        eq_(counts['ever'], 1)

        user.date_joined -= datetime.timedelta(days=6)
        user.save()
        url = reverse('manage:dashboard_data')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        counts = user_counts(response)
        eq_(counts['today'], 0)
        eq_(counts['today_delta'], 0)
        eq_(counts['this_week'], 0)
        eq_(counts['this_week_delta'], -1)
        eq_(counts['this_month'], 1)
        eq_(counts['this_month_delta'], 1)
        eq_(counts['this_year'], 1)
        eq_(counts['this_year_delta'], 1)
        eq_(counts['ever'], 1)

        month = user.date_joined.month
        while user.date_joined.month == month:
            user.date_joined -= datetime.timedelta(days=1)
        user.save()
        url = reverse('manage:dashboard_data')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        counts = user_counts(response)
        eq_(counts['today'], 0)
        eq_(counts['today_delta'], 0)
        eq_(counts['this_week'], 0)
        eq_(counts['this_week_delta'], 0)
        eq_(counts['this_month'], 0)
        eq_(counts['this_month_delta'], -1)
        eq_(counts['this_year'], 1)
        eq_(counts['this_year_delta'], 1)
        eq_(counts['ever'], 1)

        year = user.date_joined.year
        while user.date_joined.year == year:
            user.date_joined -= datetime.timedelta(days=30)
        user.save()
        url = reverse('manage:dashboard_data')
        response = self.client.get(url)
        eq_(response.status_code, 200)
        counts = user_counts(response)
        eq_(counts['today'], 0)
        eq_(counts['today_delta'], 0)
        eq_(counts['this_week'], 0)
        eq_(counts['this_week_delta'], 0)
        eq_(counts['this_month'], 0)
        eq_(counts['this_month_delta'], 0)
        eq_(counts['this_year'], 0)
        eq_(counts['this_year_delta'], -1)
        eq_(counts['ever'], 1)

    def test_cache_busting_headers(self):
        # viewing any of the public pages should NOT have it
        response = self.client.get('/')
        eq_(response.status_code, 200)
        ok_('no-store' not in response.get('Cache-Control', ''))

        response = self.client.get(reverse('manage:dashboard'))
        eq_(response.status_code, 200)
        ok_('no-store' in response['Cache-Control'])
