from friendships.api.paginations import FriendshipPagination
from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
        self.clear_cache()
        # self.anonymous_client = APIClient()
        self.haiming = self.create_user('haiming')
        self.haiming_client = APIClient()
        self.haiming_client.force_authenticate(self.haiming)

        self.bentley = self.create_user('bentley')
        self.bentley_client = APIClient()
        self.bentley_client.force_authenticate(self.bentley)

        # create followings and followers for bentley
        for i in range(2):
            follower = self.create_user('bentley_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.bentley)
        for i in range(3):
            following = self.create_user('bentley_following{}'.format(i))
            Friendship.objects.create(from_user=self.bentley, to_user=following)

    def test_follow(self):
        url = FOLLOW_URL.format(self.haiming.id)

        # must login before follow others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # return 405 if try to follow by GET
        response = self.bentley_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot follow yourself
        response = self.haiming_client.post(url)
        self.assertEqual(response.status_code, 400)
        # successfully follow, return 201
        response = self.bentley_client.post(url)
        self.assertEqual(response.status_code, 201)
        # follow the same person for more than once
        response = self.bentley_client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['duplicate'], True)
        # Friendship from A-B and from B-A are not equal
        count = Friendship.objects.count()
        response = self.haiming_client.post(FOLLOW_URL.format(self.bentley.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Friendship.objects.count(), count + 1)

    def test_unfollow(self):
        url = UNFOLLOW_URL.format(self.haiming.id)

        # must login before unfollow others
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 403)
        # return 405 if try to unfollow by GET
        response = self.bentley_client.get(url)
        self.assertEqual(response.status_code, 405)
        # cannot unfollow yourself
        response = self.haiming_client.post(url)
        self.assertEqual(response.status_code, 400)
        # unfollow successfully
        Friendship.objects.create(from_user=self.bentley, to_user=self.haiming)
        count = Friendship.objects.count()
        response = self.bentley_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(Friendship.objects.count(), count - 1)
        # unfollow the same person for more than once
        count = Friendship.objects.count()
        response = self.bentley_client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(Friendship.objects.count(), count)

    def test_followings(self):
        url = FOLLOWINGS_URL.format(self.bentley.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # make sure the ordering is in reverse chronological order
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        ts2 = response.data['results'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'bentley_following2',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'bentley_following1',
        )
        self.assertEqual(
            response.data['results'][2]['user']['username'],
            'bentley_following0',
        )

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.bentley.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # make sure the ordering is in reverse chronological order
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'bentley_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'bentley_follower0',
        )

    def test_followers_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            follower = self.create_user('haiming_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.haiming)
            if follower.id % 2 == 0:
                Friendship.objects.create(from_user=self.bentley, to_user=follower)

        url = FOLLOWERS_URL.format(self.haiming.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # bentley has followed users with even id
        response = self.bentley_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        max_page_size = FriendshipPagination.max_page_size
        page_size = FriendshipPagination.page_size
        for i in range(page_size * 2):
            following = self.create_user('haiming_following{}'.format(i))
            Friendship.objects.create(from_user=self.haiming, to_user=following)
            if following.id % 2 == 0:
                Friendship.objects.create(from_user=self.bentley, to_user=following)

        url = FOLLOWINGS_URL.format(self.haiming.id)
        self._test_friendship_pagination(url, page_size, max_page_size)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # bentley has followed users with even id
        response = self.bentley_client.get(url, {'page': 1})
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # haiming has followed all his following users
        response = self.haiming_client.get(url, {'page': 1})
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

    def _test_friendship_pagination(self, url, page_size, max_page_size):
        response = self.anonymous_client.get(url, {'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        response = self.anonymous_client.get(url, {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 2)
        self.assertEqual(response.data['has_next_page'], False)

        response = self.anonymous_client.get(url, {'page': 3})
        self.assertEqual(response.status_code, 404)

        # test user can not customize page_size exceeds max_page_size
        response = self.anonymous_client.get(url, {'page': 1, 'size': max_page_size + 1})
        self.assertEqual(len(response.data['results']), max_page_size)
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)

        # test user can customize page size by param size
        response = self.anonymous_client.get(url, {'page': 1, 'size': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['total_pages'], page_size)
        self.assertEqual(response.data['total_results'], page_size * 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertEqual(response.data['has_next_page'], True)