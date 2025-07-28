import logging
from typing import Optional, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from db.models import Company


class DAOIntegrityError(Exception):
    def __init__(
        self,
        entity: str,
        key: Union[str, UUID, int, None],
        original: Exception
    ) -> None:
        self.entity = entity
        self.key = key
        self.original = original

        msg = f"{entity}({key}) failed integrity check: {original}"
        super().__init__(msg)


class CompanyDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new(self, company: Company) -> Company:
        self.session.add(company)

        try:
            await self.session.commit()
        except IntegrityError as e:
            logging.warning(f"IntegrityError while creating Company(id={company.id}): {e}")
            await self.session.rollback()
            raise DAOIntegrityError("Company", company.id, e) from e

        return company

    async def get_by_name(self, company_name: str) -> Optional[Company]:
        stmt = select(Company).where(Company.name == company_name)

        result = await self.session.execute(stmt)
        data = result.scalar()

        return data
