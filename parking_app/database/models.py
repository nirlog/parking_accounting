from datetime import UTC, date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from parking_app.database.db import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    surname: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(128))
    patronymic: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    state_number: Mapped[str] = mapped_column(String(32))
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    color: Mapped[str | None] = mapped_column(String(128), nullable=True)
    photo_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class ParkingPlace(Base):
    __tablename__ = "parking_places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    place_number: Mapped[str] = mapped_column(String(32), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="free")
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class ParkingCard(Base):
    __tablename__ = "parking_cards"
    __table_args__ = (
        Index(
            "ux_parking_cards_active_place",
            "place_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
        ),
        Index(
            "ux_parking_cards_active_vehicle",
            "vehicle_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
        ),
        Index(
            "ux_parking_cards_active_state_number",
            "vehicle_state_number",
            unique=True,
            sqlite_where=text("status = 'active' AND vehicle_state_number IS NOT NULL AND trim(vehicle_state_number) <> ''"),
        ),
        CheckConstraint(
            "status != 'active' OR (vehicle_state_number IS NOT NULL AND trim(vehicle_state_number) <> '')",
            name="ck_parking_cards_active_vehicle_state_number_not_null",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    card_number: Mapped[str] = mapped_column(String(64), unique=True)
    paper_card_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    place_id: Mapped[int] = mapped_column(ForeignKey("parking_places.id"))
    start_date: Mapped[date] = mapped_column(Date)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    vehicle_state_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    attendant_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_with_active_paid_period: Mapped[bool] = mapped_column(Boolean, default=False)
    refund_days: Mapped[int] = mapped_column(Integer, default=0)
    refund_amount_kopecks: Mapped[int] = mapped_column(Integer, default=0)
    refund_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    parking_card_id: Mapped[int] = mapped_column(ForeignKey("parking_cards.id"))
    payment_date: Mapped[date] = mapped_column(Date)
    period_from: Mapped[date] = mapped_column(Date)
    period_to: Mapped[date] = mapped_column(Date)
    amount_kopecks: Mapped[int] = mapped_column(Integer)
    receipt_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    fiscal_number: Mapped[str | None] = mapped_column(String(128), nullable=True)
    accepted_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
