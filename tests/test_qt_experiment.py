"""Contract for shared UI state; runs only when the optional PySide6 is present."""
import pytest

pytest.importorskip('PySide6')

from qt_experiment.common import PrototypeState, row_from_snapshot
from server_monitor import Player, Snapshot


def test_snapshot_preserves_real_states_and_colored_names():
    state = PrototypeState()
    state.update_snapshot(Snapshot(address='example:28960', state='limited', map_name='Toujane'))
    assert state.rows[0]['state'] == 'limited'
    assert state.players == []
    state.update_snapshot(Snapshot(address='example:28960', state='online', map_name='Carentan',
                                   players=(Player('^1Red^7 Player', 3, 40),)))
    assert state.selected == 'example:28960'
    assert state.rows[0]['map'] == 'Carentan'
    assert 'color:#E56A61' in state.players[0]['richName']
    state.update_snapshot(Snapshot(address='example:28960', state='offline'))
    assert state.rows[0]['state'] == 'offline'
    assert state.players == []


def test_selection_survives_partial_update_and_controls_emit():
    state = PrototypeState()
    state.update_snapshot(Snapshot(address='a:28960', state='waiting'))
    state.update_snapshot(Snapshot(address='b:28960', state='waiting'))
    state.select('b:28960')
    state.update_snapshot(Snapshot(address='a:28960', state='online'))
    assert state.selected == 'b:28960'
    seen = []
    state.action.connect(seen.append)
    state.toggle('f8')
    state.request('refresh')
    assert state.f8 is False
    assert seen == ['f8', 'refresh']
