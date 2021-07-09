from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification


class NotificationServiceTests(TestCase):

    def setUp(self):
        self.haiming = self.create_user('haiming')
        self.bentley = self.create_user('bentley')
        self.haiming_tweet = self.create_tweet(self.haiming)

    def test_send_comment_notification(self):
        # do not dispatch notification if tweet user == comment user
        comment = self.create_comment(self.haiming, self.haiming_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        comment = self.create_comment(self.bentley, self.haiming_tweet)
        NotificationService.send_comment_notification(comment)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not dispatch notification if tweet user == like user
        like = self.create_like(self.haiming, self.haiming_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification if tweet user != comment user
        like = self.create_like(self.bentley, self.haiming_tweet)
        NotificationService.send_like_notification(like)
        self.assertEqual(Notification.objects.count(), 1)