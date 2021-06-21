from newsfeeds.models import NewsFeed
from friendships.models import Friendship
from rest_framework.test import APIClient
from testing.testcases import TestCase


NEWSFEEDS_URL = '/api/newsfeeds/'
POST_TWEETS_URL = '/api/tweets/'
FOLLOW_URL = '/api/friendships/{}/follow/'


class NewsFeedApiTests(TestCase):

    def setUp(self):
        self.haiming = self.create_user('haiming')
        self.haiming_client = APIClient()
        self.haiming_client.force_authenticate(self.haiming)

        self.bentley = self.create_user('bentley')
        self.bentley_client = APIClient()
        self.bentley_client.force_authenticate(self.bentley)

        # create followings and followers for bentley
        # for i in range(2):
        #     follower = self.create_user('bentley_follower{}'.format(i))
        #     Friendship.objects.create(from_user=follower, to_user=self.bentley)
        # for i in range(3):
        #     following = self.create_user('bentley_following{}'.format(i))
        #     Friendship.objects.create(from_user=self.bentley, to_user=following)

    def test_list(self):
        # 需要登录
        response = self.anonymous_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 403)
        # 不能用 post
        response = self.haiming_client.post(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 405)
        # 一开始啥都没有
        response = self.haiming_client.get(NEWSFEEDS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeeds']), 0)
        # 自己发的信息是可以看到的
        self.haiming_client.post(POST_TWEETS_URL, {'content': 'Hello World'})
        response = self.haiming_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 1)
        # 关注之后可以看到别人发的
        self.haiming_client.post(FOLLOW_URL.format(self.bentley.id))
        response = self.bentley_client.post(POST_TWEETS_URL, {
            'content': 'Hello Twitter',
        })
        posted_tweet_id = response.data['id']
        response = self.haiming_client.get(NEWSFEEDS_URL)
        self.assertEqual(len(response.data['newsfeeds']), 2)
        self.assertEqual(response.data['newsfeeds'][0]['tweet']['id'], posted_tweet_id)