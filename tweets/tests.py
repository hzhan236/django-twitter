from django.contrib.auth.models import User
from tweets.models import Tweet
from datetime import timedelta
from utils.time_helpers import utc_now
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import TweetPhoto


class TweetTests(TestCase):
    def setUp(self):
        self.haiming = self.create_user('haiming')
        self.tweet = self.create_tweet(self.haiming, content='Jiuzhang Dafa Hao')

    def test_hours_to_now(self):
        self.tweet.created_at = utc_now() - timedelta(hours=10)
        self.tweet.save()
        self.assertEqual(self.tweet.hours_to_now, 10)

    def test_like_set(self):
        self.create_like(self.haiming, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        self.create_like(self.haiming, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 1)

        bentley = self.create_user('bentley')
        self.create_like(bentley, self.tweet)
        self.assertEqual(self.tweet.like_set.count(), 2)

    def test_create_photo(self):
        # 测试可以成功创建 photo 的数据对象
        photo = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.haiming,
        )
        self.assertEqual(photo.user, self.haiming)
        self.assertEqual(photo.status, TweetPhotoStatus.PENDING)
        self.assertEqual(self.tweet.tweetphoto_set.count(), 1)