from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import exc as sa_exc, and_, or_, delete as sa_delete # SQLAlchemy exceptions and operators
from sqlalchemy.orm import selectinload # İlişkili objeleri eager load etmek için

from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_service import AppointmentService
from app.models.company_service import CompanyService # Hizmetlerin varlığını kontrol etmek için
from app.models.user import User # Kullanıcının varlığını kontrol etmek için
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentServiceSchema
from typing import Optional, List
from datetime import datetime
from uuid import UUID
import logging
logger = logging.getLogger(__name__)

async def get_appointment_by_id(db: AsyncSession, appointment_id: UUID) -> Optional[Appointment]:
    """
    Veritabanından UUID ID'sine göre bir randevu getirir.
    İlişkili kullanıcı ve hizmet detaylarını da yükler.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        appointment_id (UUID): Aranacak randevunun UUID ID'si.

    Returns:
        Optional[Appointment]: Bulunursa Appointment nesnesi, aksi takdirde None.
    """
    logger.debug(f"Getting appointment by ID: {appointment_id}")
    result = await db.execute(
        select(Appointment)
        .filter(Appointment.id == appointment_id)
        .options(selectinload(Appointment.user)) # Kullanıcıyı eager load et
        .options(selectinload(Appointment.services)) # Hizmetleri eager load et
        .options(selectinload(Appointment.appointment_services)) # Ara tabloyu eager load et
    )
    return result.scalars().first()

async def get_appointments(
    db: AsyncSession,
    user_id: Optional[UUID] = None,
    company_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[AppointmentStatus] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Appointment]:
    """
    Randevuları filtreleme ve sayfalama ile listeler.
    İlişkili kullanıcı ve hizmet detaylarını da yükler.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        user_id (Optional[UUID]): Belirli bir kullanıcıya ait randevuları filtrelemek için.
        company_id (Optional[int]): Belirli bir şirkete ait randevuları filtrelemek için.
        start_date (Optional[datetime]): Randevu başlangıç zamanının bu tarihten sonra olması için.
        end_date (Optional[datetime]): Randevu bitiş zamanının bu tarihten önce olması için.
        status (Optional[AppointmentStatus]): Randevu durumuna göre filtrelemek için.
        skip (int): Kaç kaydın atlanacağı.
        limit (int): Kaç kaydın döndürüleceği.

    Returns:
        List[Appointment]: Randevuların listesi.
    """
    logger.debug(f"Getting appointments with filters: user_id={user_id}, company_id={company_id}, start_date={start_date}, end_date={end_date}, status={status}, skip={skip}, limit={limit}")
    query = select(Appointment) \
        .options(selectinload(Appointment.user)) \
        .options(selectinload(Appointment.services)) \
        .options(selectinload(Appointment.appointment_services))

    if user_id:
        query = query.filter(Appointment.user_id == user_id)
    if company_id:
        query = query.filter(Appointment.company_id == company_id)
    if start_date:
        query = query.filter(Appointment.appointment_time >= start_date)
    if end_date:
        query = query.filter(Appointment.end_time <= end_date)
    if status:
        query = query.filter(Appointment.status == status)
    
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def check_appointment_conflict(
    db: AsyncSession,
    user_id: UUID,
    appointment_time: datetime,
    end_time: datetime,
    exclude_appointment_id: Optional[UUID] = None
) -> bool:
    """
    Belirli bir kullanıcı için verilen zaman aralığında çakışan bir randevu olup olmadığını kontrol eder.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        user_id (UUID): Randevuyu oluşturan kullanıcının ID'si.
        appointment_time (datetime): Randevunun başlangıç zamanı.
        end_time (datetime): Randevunun bitiş zamanı.
        exclude_appointment_id (Optional[UUID]): Güncellenen randevu ise, kendisini kontrol dışında bırakmak için ID.

    Returns:
        bool: Çakışma varsa True, yoksa False.
    """
    logger.debug(f"Checking for appointment conflict for user {user_id} between {appointment_time} and {end_time}")
    query = select(Appointment).filter(
        Appointment.user_id == user_id,
        Appointment.status != AppointmentStatus.cancelled, # İptal edilmiş randevuları dikkate alma
        # Randevu zaman aralıklarının çakışıp çakışmadığını kontrol et
        # (StartA < EndB) AND (EndA > StartB)
        and_(
            Appointment.appointment_time < end_time,
            Appointment.end_time > appointment_time
        )
    )
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    result = await db.execute(query)
    return result.scalars().first() is not None

async def create_appointment(db: AsyncSession, appointment_in: AppointmentCreate) -> Appointment:
    """
    Yeni bir randevu kaydı oluşturur ve ilişkili hizmetleri ekler.
    Randevu zamanı çakışması, kullanıcı ve hizmet varlığı kontrolü yapar.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        appointment_in (AppointmentCreate): Randevu oluşturma verilerini içeren Pydantic şeması.

    Returns:
        Appointment: Oluşturulan Appointment nesnesi.
    Raises:
        ValueError: Kullanıcı, şirket, hizmet bulunamazsa veya randevu çakışması olursa.
    """
    logger.info(f"Attempting to create appointment for user ID: {appointment_in.user_id} at {appointment_in.appointment_time}")

    # 1. Kullanıcının varlığını kontrol et
    from app.crud.crud_user import get_user_by_id # Dairesel bağımlılığı önlemek için burada import et
    user = await get_user_by_id(db, appointment_in.user_id)
    if not user:
        logger.warning(f"Appointment creation failed: User ID {appointment_in.user_id} not found.")
        raise ValueError("User not found.")

    # 2. Şirketin varlığını kontrol et (isteğe bağlı, eğer şirket ID'si doğrudan veriliyorsa)
    from app.crud.crud_company import get_company_by_id
    company = await get_company_by_id(db, appointment_in.company_id)
    if not company:
        logger.warning(f"Appointment creation failed: Company ID {appointment_in.company_id} not found.")
        raise ValueError("Company not found.")

    # 3. Randevu zamanı çakışması kontrolü
    if await check_appointment_conflict(db, appointment_in.user_id, appointment_in.appointment_time, appointment_in.end_time):
        logger.warning(f"Appointment creation failed: Conflict detected for user {appointment_in.user_id} at {appointment_in.appointment_time}.")
        raise ValueError("Appointment time conflict for this user.")

    # 4. Hizmetlerin varlığını ve şirkete aitliğini kontrol et
    valid_service_ids = []
    for service_data in appointment_in.services:
        service = await db.execute(select(CompanyService).filter(
            CompanyService.id == service_data.company_service_id,
            CompanyService.company_id == appointment_in.company_id, # Hizmetin randevunun ait olduğu şirkete ait olduğunu kontrol et
            CompanyService.is_active == True # Sadece aktif hizmetleri kabul et
        ))
        db_service = service.scalars().first()
        if not db_service:
            logger.warning(f"Appointment creation failed: Service ID {service_data.company_service_id} not found or inactive for company {appointment_in.company_id}.")
            raise ValueError(f"Service ID {service_data.company_service_id} not found or inactive for the specified company.")
        valid_service_ids.append(service_data) # Geçerli hizmet verilerini sakla

    if not valid_service_ids:
        raise ValueError("No valid services provided for the appointment.")

    # 5. Randevu nesnesini oluştur
    db_appointment = Appointment(
        user_id=appointment_in.user_id,
        company_id=appointment_in.company_id,
        appointment_time=appointment_in.appointment_time,
        end_time=appointment_in.end_time,
        notes=appointment_in.notes
    )
    db.add(db_appointment)
    await db.flush() # ID'yi almak için flush et

    # 6. Randevu ile hizmetleri ilişkilendir (appointment_services tablosuna ekle)
    for service_data in valid_service_ids:
        db_appointment_service = AppointmentService(
            appointment_id=db_appointment.id,
            company_service_id=service_data.company_service_id,
            quantity=service_data.quantity,
            price_at_booking=service_data.price_at_booking
        )
        db.add(db_appointment_service)
    
    try:
        await db.commit()
        await db.refresh(db_appointment)
        # İlişkili objeleri yüklemek için (eager loading veya sonraki sorgularda join)
        # create_appointment'tan sonra tekrar çekmek gerekebilir eğer ilişkiler commit sonrası yüklenmiyorsa
        # veya get_appointment_by_id'yi çağırabilirsiniz.
        created_appointment = await get_appointment_by_id(db, db_appointment.id)
        logger.info(f"Appointment (ID: {db_appointment.id}) created successfully for user ID: {db_appointment.user_id}.")
        return created_appointment
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during appointment creation: {e}", exc_info=True)
        # chk_appointment_time_order kontrolü burada yakalanabilir
        if "chk_appointment_time_order" in str(e):
            raise ValueError("Appointment end time must be after start time.")
        raise ValueError("Database error during appointment creation.")


async def update_appointment(
    db: AsyncSession,
    db_appointment: Appointment,
    appointment_update: AppointmentUpdate
) -> Appointment:
    """
    Randevu bilgilerini günceller ve ilişkili hizmetleri yönetir.
    Randevu zamanı güncelleniyorsa çakışma kontrolü yapar.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_appointment (Appointment): Veritabanından çekilmiş mevcut Appointment nesnesi.
        appointment_update (AppointmentUpdate): Güncellenecek verileri içeren Pydantic şeması.

    Returns:
        Appointment: Güncellenmiş Appointment nesnesi.
    Raises:
        ValueError: Randevu çakışması olursa veya hizmet bulunamazsa.
    """
    logger.info(f"Updating appointment ID: {db_appointment.id}")
    update_data = appointment_update.model_dump(exclude_unset=True)

    # Randevu zamanı güncelleniyorsa çakışma kontrolü
    new_appointment_time = update_data.get("appointment_time", db_appointment.appointment_time)
    new_end_time = update_data.get("end_time", db_appointment.end_time)

    if new_appointment_time != db_appointment.appointment_time or \
       new_end_time != db_appointment.end_time:
        if await check_appointment_conflict(
            db,
            db_appointment.user_id,
            new_appointment_time,
            new_end_time,
            exclude_appointment_id=db_appointment.id # Kendisini kontrol dışında bırak
        ):
            logger.warning(f"Appointment update failed for ID {db_appointment.id}: Conflict detected with new time {new_appointment_time}.")
            raise ValueError("Appointment time conflict with existing appointments.")

    # Randevu ana bilgilerini güncelle
    for key, value in update_data.items():
        if key == "services": # Hizmetler ayrı yönetilecek
            continue
        setattr(db_appointment, key, value)
    
    # Hizmet ilişkilerini güncelle (Many-to-Many için)
    if "services" in update_data and update_data["services"] is not None:
        logger.debug(f"Updating services for appointment ID: {db_appointment.id}")
        # Mevcut ilişkileri sil
        await db.execute(sa_delete(AppointmentService).filter(
            AppointmentService.appointment_id == db_appointment.id
        ))
        
        # Yeni ilişkileri ekle
        valid_new_services = []
        for service_data in update_data["services"]:
            service = await db.execute(select(CompanyService).filter(
                CompanyService.id == service_data.company_service_id,
                CompanyService.company_id == db_appointment.company_id, # Hizmetin aynı şirkete ait olduğunu kontrol et
                CompanyService.is_active == True
            ))
            db_service = service.scalars().first()
            if not db_service:
                logger.warning(f"Appointment update failed: Service ID {service_data.company_service_id} not found or inactive for company {db_appointment.company_id}.")
                raise ValueError(f"Service ID {service_data.company_service_id} not found or inactive for the specified company.")
            
            db_appointment_service = AppointmentService(
                appointment_id=db_appointment.id,
                company_service_id=service_data.company_service_id,
                quantity=service_data.quantity,
                price_at_booking=service_data.price_at_booking
            )
            db.add(db_appointment_service)
            valid_new_services.append(db_appointment_service) # Eager load için

    db.add(db_appointment)
    try:
        await db.commit()
        await db.refresh(db_appointment)
        # Güncellenmiş randevuyu ilişkili objelerle birlikte tekrar çek
        updated_appointment = await get_appointment_by_id(db, db_appointment.id)
        logger.info(f"Appointment ID {db_appointment.id} updated successfully.")
        return updated_appointment
    except sa_exc.IntegrityError as e:
        await db.rollback()
        logger.error(f"Database integrity error during appointment update for ID {db_appointment.id}: {e}", exc_info=True)
        if "chk_appointment_time_order" in str(e):
            raise ValueError("Appointment end time must be after start time.")
        if "uq_appointment_service_appointment_id_company_service_id" in str(e): # Ara tablonun unique constraint'i
            raise ValueError("Duplicate service found for this appointment.")
        raise ValueError("Database error during appointment update.")


async def cancel_appointment(db: AsyncSession, db_appointment: Appointment) -> Appointment:
    """
    Belirtilen randevunun durumunu 'cancelled' olarak günceller.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_appointment (Appointment): İptal edilecek Appointment nesnesi.

    Returns:
        Appointment: Güncellenmiş Appointment nesnesi.
    Raises:
        ValueError: Randevu zaten tamamlanmış veya iptal edilmişse.
    """
    logger.info(f"Attempting to cancel appointment ID: {db_appointment.id}")
    if db_appointment.status == AppointmentStatus.completed:
        raise ValueError("Cannot cancel a completed appointment.")
    if db_appointment.status == AppointmentStatus.cancelled:
        raise ValueError("Appointment is already cancelled.")

    db_appointment.status = AppointmentStatus.cancelled
    db.add(db_appointment)
    await db.commit()
    await db.refresh(db_appointment)
    logger.info(f"Appointment ID {db_appointment.id} cancelled successfully.")
    return db_appointment

async def delete_appointment(db: AsyncSession, db_appointment: Appointment):
    """
    Belirtilen randevuyu veritabanından siler.
    İlişkili appointment_service kayıtları CASCADE DELETE ile otomatik silinecektir.

    Args:
        db (AsyncSession): Veritabanı oturumu.
        db_appointment (Appointment): Silinecek Appointment nesnesi.
    """
    logger.info(f"Deleting appointment ID: {db_appointment.id}")
    await db.delete(db_appointment)
    await db.commit()
    logger.info(f"Appointment ID {db_appointment.id} deleted successfully.")