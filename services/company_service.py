import logging
from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from db.dao.company_dao import CompanyDAO
from db.models import Company


class CompanyService:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    async def create_new(self, name: str, location: str, description: str, link: str) -> None:
        async with self.session_maker() as session:
            company_dao = CompanyDAO(session)
            company_obj = Company(
                name=name,
                location=location,
                description=description,
                link=link
            )

            data = await company_dao.create_new(company_obj)
            logging.info(f"Created Company: id={data.id}; name={data.name}; location={data.location}; description={data.description}; link={data.link}")

    async def get_by_name(self, company_name: str) -> Optional[Company]:
        async with self.session_maker() as session:
            company_dao = CompanyDAO(session)
            return await company_dao.get_by_name(company_name)