import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from app import ControlApp
from server_monitor import Player, Server, Snapshot


class FriendNoticeTests(unittest.TestCase):
    def test_only_new_presence_after_baseline_notifies_once(self):
        app=ControlApp.__new__(ControlApp)
        app.monitor_settings={"friends":["KriS"],"servers":[Server("test:28960","Test")],
                              "notify_friends":True}
        app._friend_presence={}
        app._friend_notice_at={}
        app._friend_notifier=Mock()
        app.ui_language="ru"
        def snapshot(players):
            return Snapshot("test:28960",state="online",players=tuple(players),
                            last_success=datetime.now(timezone.utc))
        friend=Player("^1Kri^7S",2,44)
        app._server_friend_update(snapshot([friend]))
        app._server_friend_update(snapshot([]))
        app._server_friend_update(snapshot([friend]))
        app._server_friend_update(snapshot([friend]))
        app._friend_notifier.show.assert_called_once()
        self.assertIn("KriS",app._friend_notifier.show.call_args.args[1])
        self.assertIn("Test",app._friend_notifier.show.call_args.args[1])


if __name__=="__main__":
    unittest.main()
