import unittest
from unittest.mock import patch

from server_monitor import (Server, canonical_address, color_runs, dump_settings,
                            load_settings, normalized_name, plain_name, player_ping_quality, parse_response,
                            query_server)


STATUS=(b"\xff\xff\xff\xffstatusResponse\n"
        b"\\gamename\\Call of Duty 2\\sv_hostname\\^2CLASSIC ^3Oborona"
        b"\\mapname\\gob_aim\\g_gametype\\tdm\\sv_maxclients\\37\n"
        b'21 42 "^1Kri^7S"\n-1 0 "^2Medic"\n')
INFO=(b"\xff\xff\xff\xffinfoResponse\n"
      b"\\gamename\\Call of Duty 2\\clients\\0\\mapname\\toujane"
      b"\\gametype\\ctf\\sv_maxclients\\32\n")


class ProtocolTests(unittest.TestCase):
    def test_real_format_and_colors(self):
        snapshot=parse_response("146.59.34.100:28960",STATUS,37)
        self.assertEqual((snapshot.state,snapshot.map_name,snapshot.game_type),("online","gob_aim","tdm"))
        self.assertEqual((snapshot.clients,snapshot.max_clients,snapshot.ping_ms),(2,37,37))
        self.assertEqual(snapshot.players[0].name,"KriS")
        self.assertEqual((snapshot.players[0].score,snapshot.players[0].ping),(21,42))
        self.assertEqual(normalized_name("^1Kri^7S"),"kris")
        self.assertEqual(color_runs("^1Kri^7S"),(("Kri","#E56A61"),("S","#F0E8D3")))

    def test_cp1251_nickname_from_game(self):
        payload=STATUS+b'5 88 "^3'+ "Петрик".encode("cp1251") + b'"\n'
        self.assertEqual(parse_response("a:28960",payload,10).players[-1].name,"Петрик")

    def test_literal_carets_and_server_reported_zero_latency(self):
        self.assertEqual(plain_name("^^base ^xray ^2Medic"),"^base ^xray Medic")
        self.assertEqual(color_runs("^xray ^2Medic"),
                         (("^xray ","#F0E8D3"),("Medic","#87D970")))
        snapshot=parse_response("a:28960",STATUS,37)
        self.assertEqual(snapshot.players[1].ping,0)
        self.assertEqual(player_ping_quality(snapshot.players[1].ping),"server_zero")
        self.assertEqual(player_ping_quality(None),"missing")
        self.assertEqual(player_ping_quality(-1),"missing")
        self.assertEqual(player_ping_quality(46),"good")
        self.assertEqual(player_ping_quality(230),"poor")

    def test_info_is_partial_not_empty_player_list(self):
        snapshot=parse_response("example.org:28960",INFO,47)
        self.assertEqual(snapshot.state,"limited")
        self.assertEqual(snapshot.clients,0)
        self.assertEqual(snapshot.players,())

    def test_malformed_and_wrong_game(self):
        for data in (b"bad",b"\xff\xff\xff\xffprint\nhello",
                     STATUS.replace(b"Call of Duty 2",b"Quake 3")):
            with self.assertRaises(ValueError):parse_response("host:28960",data,4)

    def test_addresses_and_existing_config(self):
        self.assertEqual(canonical_address(" EXAMPLE.ORG:28961 "),"example.org:28961")
        for raw in ("", "example.com:99999", "a:b", "a:0", "http://a", "a\n"):
            with self.assertRaises(ValueError):canonical_address(raw)
        settings=load_settings({})
        self.assertEqual(settings["servers"][0].address,"146.59.34.100:28960")
        settings["servers"].append(Server("example.org:28961","Other",True))
        settings["friends"]=["KriS"]
        self.assertEqual(load_settings(dump_settings(settings))["servers"],settings["servers"])
        self.assertEqual(load_settings({"servers":[]})["servers"],[])

    def test_nonstandard_port_fields_and_udp(self):
        import socket
        import threading
        from server_monitor import address_from_fields, address_fields
        self.assertEqual(address_from_fields("148.251.139.73:12345", "28960"), "148.251.139.73:12345")
        self.assertEqual(address_fields("148.251.139.73:12345"), ("148.251.139.73", "12345"))
        for raw in ("12345", "999.251.139.73", "bad.-domain"):
            with self.assertRaises(ValueError):
                address_from_fields(raw, "28960")
        for port in ("", "0", "65536", "-1", "abc"):
            with self.assertRaises(ValueError):
                address_from_fields("localhost", port)
        addresses = [f"148.251.139.73:{p}" for p in (28960,12345,28961)]
        self.assertEqual(len(load_settings({"servers":[{"address":a} for a in addresses]})["servers"]), 3)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
            server.bind(("127.0.0.1", 0))
            port = server.getsockname()[1]
            server.settimeout(2)
            requests = []
            def reply():
                data, peer = server.recvfrom(1024)
                requests.append(data)
                server.sendto(STATUS, peer)
            worker = threading.Thread(target=reply, daemon=True)
            worker.start()
            result = query_server(address_from_fields("127.0.0.1", str(port)), timeout=.5)
            worker.join(2)
            self.assertEqual(result.state, "online")
            self.assertEqual(requests, [bytes([255])*4 + b"getstatus"])

    def test_offline_and_timeout(self):
        with patch("server_monitor.socket.getaddrinfo",side_effect=OSError("offline")):
            result=query_server("example.org:28960",timeout=.05)
        self.assertEqual(result.state,"offline")
        self.assertIsNone(result.clients)
        self.assertIsNone(result.last_success)


if __name__=="__main__":
    unittest.main()
