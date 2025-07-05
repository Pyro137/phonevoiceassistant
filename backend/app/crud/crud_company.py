from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exc as sa_exc # SQLAlchemy exceptions for integrity errors
from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate
from typing import Optional, List
import logging
logger = logging.getLogger(__name__)

async def get_company_by_id(db: AsyncSession, company_id: int) -> Optional[Company]:
    """
    Veritabanından ID'sine göre bir şirket getirir.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        company_id (int): Aranacak şirketin ID'si.

    Returns:
        Optional[Company]: Bulunursa Company nesnesi, aksi takdirde None.
    """
    logger.debug(f"Getting company by ID: {company_id}")
    result = await db.execute(select(Company).filter(Company.id == company_id))
    return result.scalars().first()

async def get_company_by_name(db: AsyncSession, name: str) -> Optional[Company]:
    """
    Veritabanından ismine göre bir şirket getirir.
    Benzersizlik kontrolü için kullanılır.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        name (str): Aranacak şirketin adı.

    Returns:
        Optional[Company]: Bulunursa Company nesnesi, aksi takdirde None.
    """
    logger.debug(f"Getting company by name: {name}")
    result = await db.execute(select(Company).filter(Company.name == name))
    return result.scalars().first()

async def get_company_by_email(db: AsyncSession, email: str) -> Optional[Company]:
    """
    Veritabanından e-posta adresine göre bir şirket getirir.
    Benzersizlik kontrolü için kullanılır.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        email (str): Aranacak şirketin e-posta adresi.

    Returns:
        Optional[Company]: Bulunursa Company nesnesi, aksi takdirde None.
    """
    logger.debug(f"Getting company by email: {email}")
    result = await db.execute(select(Company).filter(Company.email == email))
    return result.scalars().first()

async def get_all_companies(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None # Aktiflik durumuna göre filtreleme eklendi
) -> List[Company]:
    """
    Şirketleri filtreleme ve sayfalama ile listeler.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        skip (int): Kaç kaydın atlanacağı.
        limit (int): Kaç kaydın döndürüleceği.
        is_active (Optional[bool]): Şirketlerin aktiflik durumuna göre filtrelemek için.

    Returns:
        List[Company]: Şirketlerin listesi.
    """
    logger.debug(f"Getting all companies with skip: {skip}, limit: {limit}, is_active: {is_active}")
    query = select(Company)
    if is_active is not None:
        query = query.filter(Company.is_active == is_active)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def create_company(db: AsyncSession, company_in: CompanyCreate) -> Company:
    """
    Yeni bir şirket kaydı oluşturur.
    Şirket adı ve e-posta benzersizliğini kontrol eder.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        company_in (CompanyCreate): Şirket oluşturma verilerini içeren Pydantic şeması.

    Returns:
        Company: Oluşturulan Company nesnesi.
    Raises:
        ValueError: Eğer şirket adı veya e-postası zaten mevcutsa.
    """
    logger.info(f"Attempting to create company: {company_in.name}")
    
    # Benzersizlik kontrolleri (DB constraint'leri olsa da, daha erken hata yakalamak için)
    if await get_company_by_name(db, company_in.name):
        logger.warning(f"Company creation failed: Name '{company_in.name}' already exists.")
        raise ValueError("Company with this name already exists.")
    if company_in.email and await get_company_by_email(db, company_in.email):
        logger.warning(f"Company creation failed: Email '{company_in.email}' already exists.")
        raise ValueError("Company with this email already exists.")

    db_company = Company(
        name=company_in.name,
        phone=company_in.phone,
        email=company_in.email,
        address=company_in.address
    )
    db.add(db_company)
    try:
        await db.commit()
        await db.refresh(db_company)
        logger.info(f"Company '{db_company.name}' (ID: {db_company.id}) created successfully.")
        return db_company
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during company creation: {e}", exc_info=True)
        # Daha spesifik bir hata mesajı için e.orig'i kontrol edebilirsiniz.
        if "unique_company_name_key" in str(e) or "company_name_key" in str(e):
            raise ValueError("Company with this name already exists.")
        if "company_email_key" in str(e):
            raise ValueError("Company with this email already exists.")
        raise ValueError("Database error during company creation.")


async def update_company(db: AsyncSession, db_company: Company, company_update: CompanyUpdate) -> Company:
    """
    Şirket bilgilerini günceller.
    Şirket adı veya e-postası güncelleniyorsa benzersizliğini kontrol eder.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_company (Company): Veritabanından çekilmiş mevcut Company nesnesi.
        company_update (CompanyUpdate): Güncellenecek verileri içeren Pydantic şeması.

    Returns:
        Company: Güncellenmiş Company nesnesi.
    Raises:
        ValueError: Eğer güncellenen şirket adı veya e-postası zaten mevcutsa.
    """
    logger.info(f"Updating company ID: {db_company.id}")
    update_data = company_update.model_dump(exclude_unset=True)

    # Ad veya e-posta güncelleniyorsa benzersizlik kontrolü
    if "name" in update_data and update_data["name"] != db_company.name:
        if await get_company_by_name(db, update_data["name"]):
            logger.warning(f"Company update failed for ID {db_company.id}: Name '{update_data['name']}' already exists.")
            raise ValueError("Company with this name already exists.")
    
    if "email" in update_data and update_data["email"] != db_company.email:
        if update_data["email"] and await get_company_by_email(db, update_data["email"]):
            logger.warning(f"Company update failed for ID {db_company.id}: Email '{update_data['email']}' already exists.")
            raise ValueError("Company with this email already exists.")

    for key, value in update_data.items():
        setattr(db_company, key, value)
    
    db.add(db_company)
    try:
        await db.commit()
        await db.refresh(db_company)
        logger.info(f"Company ID {db_company.id} updated successfully.")
        return db_company
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during company update for ID {db_company.id}: {e}", exc_info=True)
        if "uq_company_name_key" in str(e) or "company_name_key" in str(e):
            raise ValueError("Company with this name already exists.")
        if "company_email_key" in str(e):
            raise ValueError("Company with this email already exists.")
        raise ValueError("Database error during company update.")


async def delete_company(db: AsyncSession, db_company: Company):
    """
    Belirtilen şirketi veritabanından siler.
    İlişkili kullanıcılar ve hizmetler CASCADE DELETE ile silinecektir.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_company (Company): Silinecek Company nesnesi.
    """
    logger.info(f"Deleting company ID: {db_company.id}")
    await db.delete(db_company)
    await db.commit()
    logger.info(f"Company ID {db_company.id} deleted successfully.")