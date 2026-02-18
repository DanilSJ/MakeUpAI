from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.models import db_helper
from . import schemas
from . import crud

router = APIRouter()


@router.post("/start/", response_model=schemas.TestSchema)
async def start_test(
    data_in: schemas.RegisterSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.start_test(session=session, data_in=data_in)


@router.post("/submit/", response_model=schemas.SubTestSchema)
async def submit_test(
    data_in: schemas.SubmitSchema,
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    return await crud.submit_test(session=session, data_in=data_in)
