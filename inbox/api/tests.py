from notifications.models import Notification
from testing.testcases import TestCase


COMMENT_URL = '/api/comments/'
LIKE_URL = '/api/likes/'
NOTIFICATION_URL = '/api/notifications/'

class NotificationTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.haiming, self.haiming_client = self.create_user_and_client('haiming')
        self.bentley, self.bentley_client = self.create_user_and_client('bentley')
        self.bentley_tweet = self.create_tweet(self.bentley)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.haiming_client.post(COMMENT_URL, {
            'tweet_id': self.bentley_tweet.id,
            'content': 'a ha',
        })
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        self.haiming_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.bentley_tweet.id,
        })
        self.assertEqual(Notification.objects.count(), 1)

class NotificationApiTests(TestCase):

    def setUp(self):
        self.haiming, self.haiming_client = self.create_user_and_client('haiming')
        self.bentley, self.bentley_client = self.create_user_and_client('bentley')
        self.haiming_tweet = self.create_tweet(self.haiming)

    def test_unread_count(self):
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.haiming_tweet.id,
        })

        url = '/api/notifications/unread-count/'
        response = self.haiming_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)

        comment = self.create_comment(self.haiming, self.haiming_tweet)
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        response = self.haiming_client.get(url)
        self.assertEqual(response.data['unread_count'], 2)
        response = self.bentley_client.get(url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_mark_all_as_read(self):
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.haiming_tweet.id,
        })
        comment = self.create_comment(self.haiming, self.haiming_tweet)
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        unread_url = '/api/notifications/unread-count/'
        response = self.haiming_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        mark_url = '/api/notifications/mark-all-as-read/'
        response = self.haiming_client.get(mark_url)
        self.assertEqual(response.status_code, 405)

        # bentley cannot mark haiming's notification as read
        response = self.bentley_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 0)
        response = self.haiming_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)

        # haiming can mark his own notification as read
        response = self.haiming_client.post(mark_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['marked_count'], 2)
        response = self.haiming_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 0)

    def test_list(self):
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.haiming_tweet.id,
        })
        comment = self.create_comment(self.haiming, self.haiming_tweet)
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })

        # 匿名用户无法访问 api
        response = self.anonymous_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 403)
        # bentley 看不到任何 notifications
        response = self.bentley_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        # haiming 看到两个 notifications
        response = self.haiming_client.get(NOTIFICATION_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        # 标记之后看到一个未读
        notification = self.haiming.notifications.first()
        notification.unread = False
        notification.save()
        response = self.haiming_client.get(NOTIFICATION_URL)
        self.assertEqual(response.data['count'], 2)
        response = self.haiming_client.get(NOTIFICATION_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.haiming_client.get(NOTIFICATION_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)


    def test_update(self):
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'tweet',
            'object_id': self.haiming_tweet.id,
        })
        comment = self.create_comment(self.haiming, self.haiming_tweet)
        self.bentley_client.post(LIKE_URL, {
            'content_type': 'comment',
            'object_id': comment.id,
        })
        notification = self.haiming.notifications.first()

        url = '/api/notifications/{}/'.format(notification.id)
        # post 不行，需要用 put
        response = self.bentley_client.post(url, {'unread': False})
        self.assertEqual(response.status_code, 405)
        # 不可以被其他人改变 notification 状态
        response = self.anonymous_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 403)
        # 因为 queryset 是按照当前登陆用户来，所以会返回 404 而不是 403
        response = self.bentley_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 404)
        # 成功标记为已读
        response = self.haiming_client.put(url, {'unread': False})
        self.assertEqual(response.status_code, 200)
        unread_url = '/api/notifications/unread-count/'
        response = self.haiming_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 1)

        # 再标记为未读
        response = self.haiming_client.put(url, {'unread': True})
        response = self.haiming_client.get(unread_url)
        self.assertEqual(response.data['unread_count'], 2)
        # 必须带 unread
        response = self.haiming_client.put(url, {'verb': 'newverb'})
        self.assertEqual(response.status_code, 400)
        # 不可修改其他的信息
        response = self.haiming_client.put(url, {'verb': 'newverb', 'unread': False})
        self.assertEqual(response.status_code, 200)
        notification.refresh_from_db()
        self.assertNotEqual(notification.verb, 'newverb')