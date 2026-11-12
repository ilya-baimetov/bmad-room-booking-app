"""My bookings: a person's own bookings for a span of time.

Owns no tables (AD-3); everything comes from `bookings.service`, which also applies
AD-8 to what the viewer sees. Works in aware UTC datetimes (AD-5).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from roombooker.bookings import service as bookings_service
from roombooker.bookings.service import BookingView
from roombooker.people.service import Person


def my_bookings(
    session: Session, person: Person, start_at: datetime, end_at: datetime
) -> list[BookingView]:
    """Bookings the person organises or attends that overlap [start_at, end_at)."""
    return bookings_service.bookings_for_person(session, person, start_at, end_at)
