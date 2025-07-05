from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exc as sa_exc # SQLAlchemy exceptions for integrity errors
from app.models.company_service import CompanyService
from app.schemas.company_service import CompanyServiceCreate, CompanyServiceUpdate
from typing import Optional, List
from decimal import Decimal # Fiyatlar için Decimal tipi
import logging
logger = logging.getLogger(__name__)

async def get_company_service_by_id(db: AsyncSession, service_id: int) -> Optional[CompanyService]:
    """
    Veritabanından ID'sine göre bir şirket hizmeti getirir.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        service_id (int): Aranacak hizmetin ID'si.

    Returns:
        Optional[CompanyService]: Bulunursa CompanyService nesnesi, aksi takdirde None.
    """
    logger.debug(f"Getting company service by ID: {service_id}")
    result = await db.execute(select(CompanyService).filter(CompanyService.id == service_id))
    return result.scalars().first()

async def get_company_service_by_company_id_and_name(
    db: AsyncSession, 
    company_id: int, 
    name: str
) -> Optional[CompanyService]:
    """
    Belirli bir şirkete ait, ismine göre bir hizmeti getirir.
    Hizmet adı benzersizliği kontrolü için kullanılır.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        company_id (int): Şirketin ID'si.
        name (str): Aranacak hizmetin adı.

    Returns:
        Optional[CompanyService]: Bulunursa CompanyService nesnesi, aksi takdirde None.
    """
    logger.debug(f"Getting company service by company_id: {company_id} and name: {name}")
    result = await db.execute(
        select(CompanyService).filter(
            CompanyService.company_id == company_id,
            CompanyService.name == name
        )
    )
    return result.scalars().first()

async def get_services_by_company_id(
    db: AsyncSession,
    company_id: int,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None # Aktiflik durumuna göre filtreleme
) -> List[CompanyService]:
    """
    Belirli bir şirkete ait hizmetleri filtreleme ve sayfalama ile listeler.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        company_id (int): Hizmetleri listelenecek şirketin ID'si.
        skip (int): Kaç kaydın atlanacağı.
        limit (int): Kaç kaydın döndürüleceği.
        is_active (Optional[bool]): Hizmetlerin aktiflik durumuna göre filtrelemek için.

    Returns:
        List[CompanyService]: Şirket hizmetlerinin listesi.
    """
    logger.debug(f"Getting services for company_id: {company_id} with skip: {skip}, limit: {limit}, is_active: {is_active}")
    query = select(CompanyService).filter(CompanyService.company_id == company_id)
    if is_active is not None:
        query = query.filter(CompanyService.is_active == is_active)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def create_company_service(db: AsyncSession, service_in: CompanyServiceCreate) -> CompanyService:
    """
    Yeni bir şirket hizmeti kaydı oluşturur.
    Hizmet adı ve şirket ID'si kombinasyonunun benzersizliğini kontrol eder.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        service_in (CompanyServiceCreate): Hizmet oluşturma verilerini içeren Pydantic şeması.

    Returns:
        CompanyService: Oluşturulan CompanyService nesnesi.
    Raises:
        ValueError: Eğer aynı şirkette aynı isimde bir hizmet zaten mevcutsa.
    """
    logger.info(f"Attempting to create service '{service_in.name}' for company ID: {service_in.company_id}")
    
    # Benzersizlik kontrolü (DB constraint'i olsa da, daha erken hata yakalamak için)
    if await get_company_service_by_company_id_and_name(db, service_in.company_id, service_in.name):
        logger.warning(f"Service creation failed: Service '{service_in.name}' already exists for company ID {service_in.company_id}.")
        raise ValueError("Service with this name already exists for this company.")

    db_service = CompanyService(
        company_id=service_in.company_id,
        name=service_in.name,
        description=service_in.description,
        price=service_in.price,
        duration_minutes=service_in.duration_minutes
    )
    db.add(db_service)
    try:
        await db.commit()
        await db.refresh(db_service)
        logger.info(f"Service '{db_service.name}' (ID: {db_service.id}) created successfully for company ID: {db_service.company_id}.")
        return db_service
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during service creation: {e}", exc_info=True)
        # Benzersiz kısıtlama adını kontrol edin (SQL'deki 'uq_company_service_name_company_id')
        if "uq_company_service_name_company_id" in str(e):
            raise ValueError("Service with this name already exists for this company.")
        raise ValueError("Database error during service creation.")


async def update_company_service(db: AsyncSession, db_service: CompanyService, service_update: CompanyServiceUpdate) -> CompanyService:
    """
    Şirket hizmeti bilgilerini günceller.
    Hizmet adı güncelleniyorsa benzersizliğini kontrol eder.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_service (CompanyService): Veritabanından çekilmiş mevcut CompanyService nesnesi.
        service_update (CompanyServiceUpdate): Güncellenecek verileri içeren Pydantic şeması.

    Returns:
        CompanyService: Güncellenmiş CompanyService nesnesi.
    Raises:
        ValueError: Eğer güncellenen hizmet adı aynı şirkette zaten mevcutsa.
    """
    logger.info(f"Updating service ID: {db_service.id} for company ID: {db_service.company_id}")
    update_data = service_update.model_dump(exclude_unset=True)

    # Ad güncelleniyorsa benzersizlik kontrolü
    if "name" in update_data and update_data["name"] != db_service.name:
        if await get_company_service_by_company_id_and_name(db, db_service.company_id, update_data["name"]):
            logger.warning(f"Service update failed for ID {db_service.id}: Name '{update_data['name']}' already exists for company ID {db_service.company_id}.")
            raise ValueError("Service with this name already exists for this company.")

    for key, value in update_data.items():
        setattr(db_service, key, value)
    
    db.add(db_service)
    try:
        await db.commit()
        await db.refresh(db_service)
        logger.info(f"Service ID {db_service.id} updated successfully.")
        return db_service
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during service update for ID {db_service.id}: {e}", exc_info=True)
        if "uq_company_service_name_company_id" in str(e):
            raise ValueError("Service with this name already exists for this company.")
        raise ValueError("Database error during service update.")


async def delete_company_service(db: AsyncSession, db_service: CompanyService):
    """
    Belirtilen şirket hizmetini veritabanından siler.
    Bu işlem, eğer hizmete bağlı randevu hizmetleri (appointment_service) varsa
    veritabanı kısıtlaması (on delete RESTRICT) nedeniyle başarısız olabilir.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_service (CompanyService): Silinecek CompanyService nesnesi.
    Raises:
        ValueError: Eğer hizmete bağlı randevular varsa silinemez.
    """
    logger.info(f"Deleting company service ID: {db_service.id}")
    try:
        await db.delete(db_service)
        await db.commit()
        logger.info(f"Company service ID {db_service.id} deleted successfully.")
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during service deletion for ID {db_service.id}: {e}", exc_info=True)
        # fk_app_service_company_service kısıtlamasını kontrol edin
        if "fk_app_service_company_service" in str(e):
            raise ValueError("Cannot delete service because it is linked to existing appointments. Please remove all associated appointments first.")
        raise ValueError("Database error during service deletion.")