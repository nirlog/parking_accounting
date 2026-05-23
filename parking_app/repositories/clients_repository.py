from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from parking_app.database.models import Client


def list_clients(session: Session) -> list[Client]:
    stmt: Select[tuple[Client]] = select(Client).order_by(Client.surname, Client.name, Client.id)
    return list(session.scalars(stmt))


def get_client(session: Session, client_id: int) -> Client | None:
    return session.get(Client, client_id)


def create_client(
    session: Session,
    *,
    surname: str,
    name: str,
    patronymic: str | None = None,
    phone: str | None = None,
    document_type: str | None = None,
    document_number: str | None = None,
    address: str | None = None,
    photo_path: str | None = None,
) -> Client:
    client = Client(
        surname=surname,
        name=name,
        patronymic=patronymic,
        phone=phone,
        document_type=document_type,
        document_number=document_number,
        address=address,
        photo_path=photo_path,
    )
    session.add(client)
    session.flush()
    return client
