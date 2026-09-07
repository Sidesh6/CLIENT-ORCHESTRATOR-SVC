from src.events.bus import EventBus
from src.schemas.workflow import DomainEventPayload


def test_event_bus_publish_subscribe():
    bus = EventBus()
    received = []

    def on_lead_discovered(event: DomainEventPayload):
        received.append(event.data.get("title"))

    bus.subscribe("lead.discovered", on_lead_discovered)

    bus.publish(
        DomainEventPayload(
            event_type="lead.discovered",
            source_service="client-finder-svc",
            data={"title": "FastAPI Lead"},
        )
    )

    assert len(received) == 1
    assert received[0] == "FastAPI Lead"
    assert len(bus.get_recent_events()) == 1
