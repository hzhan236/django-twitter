from friendships.models import Friendship
from friendships.services import FriendshipService
from testing.testcases import TestCase


class FriendshipServiceTests(TestCase):

    def setUp(self):
        self.clear_cache()
        self.haiming = self.create_user('haiming')
        self.bentley = self.create_user('bentley')

    def test_get_followings(self):
        user1 = self.create_user('user1')
        user2 = self.create_user('user2')
        for to_user in [user1, user2, self.bentley]:
            Friendship.objects.create(from_user=self.haiming, to_user=to_user)

        user_id_set = FriendshipService.get_following_user_id_set(self.haiming.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id, self.bentley.id})

        Friendship.objects.filter(from_user=self.haiming, to_user=self.bentley).delete()
        user_id_set = FriendshipService.get_following_user_id_set(self.haiming.id)
        self.assertSetEqual(user_id_set, {user1.id, user2.id})