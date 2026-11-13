"""My bookings: a person's own bookings for a span of time, and their subscribed feed.

Owns no tables (AD-3); bookings come from `bookings.service`, which also applies AD-8 to
what the viewer sees, and the feed token from `people.service`, which owns it. Works in
aware UTC datetimes (AD-5).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from roombooker.bookings import service as bookings_service
from roombooker.bookings.service import BookingView
from roombooker.people import service as people_service
from roombooker.people.service import Person


def my_bookings(
    session: Session, person: Person, start_at: datetime, end_at: datetime
) -> list[BookingView]:
    """Bookings the person organises or attends that overlap [start_at, end_at)."""
    return bookings_service.bookings_for_person(session, person, start_at, end_at)


def feed(session: Session, token: str) -> str | None:
    """The feed's iCalendar text for whoever holds this token, or None when no active
    person does. The token alone identifies the person: calendar apps send no cookie."""
    person = people_service.person_for_feed_token(session, token)
    if person is None:
        return None
    return bookings_service.feed_calendar(session, person)


def feed_address_token(session: Session, person: Person) -> str | None:
    """The person's own feed token, or None until they create an address. Never writes."""
    return people_service.feed_token(session, person)


def reset_feed(session: Session, person: Person) -> str:
    """Create the person's feed token, or replace it so the old address stops working."""
    return people_service.new_feed_token(session, person)
