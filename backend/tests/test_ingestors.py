"""Tests for the NASA EONET and ReliefWeb ingestors."""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.models.event import EventType
from app.workers.ingestion.nasa_eonet import NASAEONETIngestor
from app.workers.ingestion.reliefweb import ReliefWebIngestor


# ---------------------------------------------------------------------------
# NASA EONET
# ---------------------------------------------------------------------------

_EONET_SAMPLE = {
    "events": [
        {
            "id": "EONET_6497",
            "title": "Bobcat Fire, California",
            "categories": [{"id": "wildfires", "title": "Wildfires"}],
            "sources": [{"id": "CALFIRE", "url": "https://calfire.ca.gov/test"}],
            "geometry": [
                {
                    "type": "Point",
                    "date": "2024-09-10T12:00:00Z",
                    "coordinates": [-117.9, 34.2],
                }
            ],
        },
        {
            "id": "EONET_7001",
            "title": "Mount Etna Eruption",
            "categories": [{"id": "volcanoes", "title": "Volcanoes"}],
            "sources": [],
            "geometry": [
                {
                    "type": "Point",
                    "date": "2024-09-11T08:00:00Z",
                    "coordinates": [14.98, 37.75],
                }
            ],
        },
        {
            # Event with no geometry should still be returned with defaults
            "id": "EONET_9999",
            "title": "Sea Ice Event",
            "categories": [{"id": "seaAndLakeIce", "title": "Sea and Lake Ice"}],
            "sources": [],
            "geometry": [],
        },
    ]
}


@pytest.mark.asyncio
async def test_nasa_eonet_fetch_success() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = _EONET_SAMPLE
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        ingestor = NASAEONETIngestor()
        events = await ingestor.fetch()

    assert len(events) == 3

    fire = next(e for e in events if e.source_event_id == "EONET_6497")
    assert fire.event_type == EventType.wildfire
    assert fire.lat == pytest.approx(34.2)
    assert fire.lon == pytest.approx(-117.9)
    assert fire.url == "https://calfire.ca.gov/test"
    assert "nasa-eonet" in fire.tags
    assert "wildfires" in fire.tags

    volcano = next(e for e in events if e.source_event_id == "EONET_7001")
    assert volcano.event_type == EventType.volcano

    ice = next(e for e in events if e.source_event_id == "EONET_9999")
    assert ice.event_type == EventType.other
    assert ice.lat is None
    assert ice.lon is None


@pytest.mark.asyncio
async def test_nasa_eonet_fetch_http_error() -> None:
    import httpx

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        ingestor = NASAEONETIngestor()
        events = await ingestor.fetch()

    assert events == []


@pytest.mark.asyncio
async def test_nasa_eonet_polygon_geometry() -> None:
    """Polygon geometry should compute a centroid lat/lon."""
    data = {
        "events": [
            {
                "id": "EONET_POLY",
                "title": "Polygon Fire",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "sources": [],
                "geometry": [
                    {
                        "type": "Polygon",
                        "date": "2024-09-12T00:00:00Z",
                        "coordinates": [
                            [
                                [10.0, 20.0],
                                [12.0, 20.0],
                                [12.0, 22.0],
                                [10.0, 22.0],
                                [10.0, 20.0],
                            ]
                        ],
                    }
                ],
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        events = await NASAEONETIngestor().fetch()

    assert len(events) == 1
    # Average includes the closing vertex: lons=[10,12,12,10,10] avg=10.8, lats=[20,20,22,22,20] avg=20.8
    assert events[0].lon == pytest.approx(10.8)
    assert events[0].lat == pytest.approx(20.8)


# ---------------------------------------------------------------------------
# ReliefWeb
# ---------------------------------------------------------------------------

_RELIEFWEB_SAMPLE = {
    "data": [
        {
            "id": 12345,
            "fields": {
                "name": "Afghanistan Earthquake 2024",
                "date": {"created": "2024-10-01T06:00:00+00:00"},
                "country": [{"name": "Afghanistan"}],
                "type": [{"name": "Earthquake", "code": "EQ"}],
                "status": "ongoing",
                "alert_level": "red",
                "url": "https://reliefweb.int/disaster/eq-2024-000200-afg",
                "description": "Magnitude 6.2 earthquake struck northern Afghanistan.",
                "glide": "EQ-2024-000200-AFG",
            },
        },
        {
            "id": 67890,
            "fields": {
                "name": "Sudan Conflict Crisis",
                "date": {"created": "2024-04-15T00:00:00+00:00"},
                "country": [{"name": "Sudan"}, {"name": "Chad"}],
                "type": [{"name": "Conflict", "code": "CE"}],
                "status": "alert",
                "alert_level": "orange",
                "url": "https://reliefweb.int/disaster/ce-2024-000050-sdn",
                "description": "",
            },
        },
    ]
}


@pytest.mark.asyncio
async def test_reliefweb_fetch_success() -> None:
    mock_response = MagicMock()
    mock_response.json.return_value = _RELIEFWEB_SAMPLE
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        ingestor = ReliefWebIngestor()
        events = await ingestor.fetch()

    assert len(events) == 2

    eq = next(e for e in events if e.source_event_id == "RW-12345")
    assert eq.event_type == EventType.earthquake
    assert eq.country == "Afghanistan"
    assert eq.severity == pytest.approx(0.9)
    assert "reliefweb" in eq.tags

    conflict = next(e for e in events if e.source_event_id == "RW-67890")
    assert conflict.event_type == EventType.conflict
    assert conflict.country == "Sudan"
    assert conflict.severity == pytest.approx(0.65)


@pytest.mark.asyncio
async def test_reliefweb_fetch_http_error() -> None:
    import httpx

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("timeout"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        events = await ReliefWebIngestor().fetch()

    assert events == []


@pytest.mark.asyncio
async def test_reliefweb_unknown_type_defaults_to_other() -> None:
    data = {
        "data": [
            {
                "id": 99999,
                "fields": {
                    "name": "Mystery Event",
                    "date": {"created": "2024-01-01T00:00:00+00:00"},
                    "country": [],
                    "type": [{"name": "SomethingUnknown", "code": "XX"}],
                    "status": "past",
                    "alert_level": "",
                },
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = data
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        events = await ReliefWebIngestor().fetch()

    assert len(events) == 1
    assert events[0].event_type == EventType.other
