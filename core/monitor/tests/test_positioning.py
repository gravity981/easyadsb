import monitor.app.positioning as pos
from pynmeagps import NMEAMessage
from contextlib import nullcontext as does_not_raise


def test_updateWithIgnoredMessageShouldDoNothing():
    monitor = pos.NavMonitor()
    msg = NMEAMessage("GP", "RMC", 0)
    with does_not_raise():
        monitor.update(msg)
