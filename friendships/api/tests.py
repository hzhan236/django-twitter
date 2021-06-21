from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase


FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'
FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'


class FriendshipApiTests(TestCase):

    def setUp(self):
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
        self.assertEqual(len(response.data['followings']), 3)
        # make sure the ordering is in reverse chronological order
        ts0 = response.data['followings'][0]['created_at']
        ts1 = response.data['followings'][1]['created_at']
        ts2 = response.data['followings'][2]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(ts1 > ts2, True)
        self.assertEqual(
            response.data['followings'][0]['user']['username'],
            'bentley_following2',
        )
        self.assertEqual(
            response.data['followings'][1]['user']['username'],
            'bentley_following1',
        )
        self.assertEqual(
            response.data['followings'][2]['user']['username'],
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
        self.assertEqual(len(response.data['followers']), 2)
        # make sure the ordering is in reverse chronological order
        ts0 = response.data['followers'][0]['created_at']
        ts1 = response.data['followers'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['followers'][0]['user']['username'],
            'bentley_follower1',
        )
        self.assertEqual(
            response.data['followers'][1]['user']['username'],
            'bentley_follower0',
        )