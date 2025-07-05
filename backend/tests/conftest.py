# tests/conftest.py

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch # Mocking için
from uuid import uuid4 # Sahte UUID'ler oluşturmak için
from datetime import datetime, timedelta

# Ana FastAPI uygulamanızı ve veritabanı/model base'inizi import edin
from app.main import app
from app.core.database.database import get_db, Base
from app.core.config import get_settings # Ayarları mock'lamak için

# Testler için kullanılacak in-memory SQLite veritabanı URL'si
# Bu, gerçek PostgreSQL veritabanınıza dokunmadan hızlı testler yapmanızı sağlar.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# --- Veritabanı Fixture'ları ---

@pytest.fixture(name="test_engine")
async def test_engine_fixture():
    """
    Testler için asenkron bir SQLAlchemy motoru oluşturur ve yönetir.
    Her test oturumu için temiz bir veritabanı sağlar.
    """
    # In-memory SQLite motorunu oluştur
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Tüm tabloları oluştur
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine # Testlerin motoru kullanmasına izin ver

    # Testler bittikten sonra tüm tabloları sil
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Motoru kapat
    await engine.dispose()

@pytest.fixture(name="test_db")
async def test_db_fixture(test_engine):
    """
    Testler için asenkron bir veritabanı oturumu sağlar.
    Her test için bağımsız bir oturum oluşturulur.
    """
    AsyncSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
    )
    async with AsyncSessionLocal() as session:
        yield session # Testin oturumu kullanmasına izin ver

@pytest.fixture(name="override_get_db")
async def override_get_db_fixture(test_db):
    """
    FastAPI'nin get_db bağımlılığını test veritabanı oturumuyla geçersiz kılar.
    Bu sayede API endpoint'leri test veritabanını kullanır.
    """
    async def _override_get_db():
        yield test_db
    
    # FastAPI uygulamasının get_db bağımlılığını geçersiz kıl
    app.dependency_overrides[get_db] = _override_get_db
    yield # Testlerin bu geçersiz kılmayı kullanmasına izin ver
    # Testler bittikten sonra geçersiz kılmayı kaldırarak temizle
    app.dependency_overrides.pop(get_db)

# --- FastAPI Test İstemcisi Fixture'ı ---

@pytest.fixture(name="client")
async def client_fixture(override_get_db):
    """
    FastAPI uygulamasını test etmek için asenkron bir HTTP istemcisi sağlar.
    Veritabanı bağımlılığı test veritabanıyla geçersiz kılınmıştır.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# --- Supabase Auth Mocking Fixture'ı ---

@pytest.fixture
def mock_supabase_auth(mocker):
    """
    Supabase Auth istemcisini ve ilgili metotlarını mock'lar.
    Bu, testlerin gerçek Supabase hizmetine bağımlı olmamasını sağlar.
    """
    # Sahte kullanıcı ve oturum verileri oluştur
    mock_user_id = str(uuid4()) # Rastgele bir UUID oluştur
    mock_user_email = "test@example.com"
    mock_user_name = "Test User"
    mock_user_role = "employee"
    
    # Supabase'in döndüreceği sahte kullanıcı objesi
    mock_user_obj = MagicMock()
    mock_user_obj.id = mock_user_id
    mock_user_obj.email = mock_user_email
    # Supabase Auth, kullanıcı meta verilerini 'user_metadata' içinde tutar.
    mock_user_obj.user_metadata = {"full_name": mock_user_name, "role": mock_user_role}

    # Supabase'in döndüreceği sahte oturum objesi (JWT token'ı içerir)
    mock_session_obj = MagicMock()
    # Sahte bir JWT token'ı oluştur. Bu token, security.py'deki JWT_SECRET_KEY ile uyumlu olmalı.
    # Gerçek bir JWT oluşturmak için jose kütüphanesini kullanabiliriz.
    # Payload'da 'sub' (user ID) ve 'exp' (expiration) alanları kritik.
    settings = get_settings() # Gerçek ayarları al
    mock_jwt_payload = {
        "sub": mock_user_id,
        "email": mock_user_email,
        "role": mock_user_role,
        "exp": (datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()
    }
    mock_jwt_token = jwt.encode(mock_jwt_payload, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    
    mock_session_obj.access_token = mock_jwt_token
    mock_session_obj.expires_at = mock_jwt_payload["exp"]

    # --- Supabase Auth Metotlarını Mock'lama ---

    # sign_up metodu için mock
    mock_sign_up_response = MagicMock()
    mock_sign_up_response.user = mock_user_obj
    mock_sign_up_response.session = mock_session_obj
    mocker.patch("supabase.Client.auth.sign_up", return_value=mock_sign_up_response)

    # sign_in_with_password metodu için mock
    mock_sign_in_response = MagicMock()
    mock_sign_in_response.user = mock_user_obj
    mock_sign_in_response.session = mock_session_obj
    mocker.patch("supabase.Client.auth.sign_in_with_password", return_value=mock_sign_in_response)

    # sign_out metodu için mock
    mocker.patch("supabase.Client.auth.sign_out", return_value=None)

    # update_user metodu için mock
    mock_update_user_response = MagicMock()
    mock_update_user_response.user = mock_user_obj # Güncellenmiş kullanıcı objesi
    mocker.patch("supabase.Client.auth.update_user", return_value=mock_update_user_response)

    # --- Supabase İstemcisini ve JWT Secret'ı Mock'lama ---

    # app.core.config.Settings objesinin JWT_SECRET_KEY'ini mock'la
    # Bu, security.py'deki jwt.decode çağrısının başarılı olmasını sağlar.
    # Gerçek Supabase JWT Secret'ınızla eşleşen bir test anahtarı kullanın.
    # ÖNEMLİ: Bu, settings objesinin bir örneği alındıktan sonra çalışır.
    # Eğer settings objesi global olarak import edildiyse, patch.object kullanmak daha güvenli olabilir.
    # Şimdilik doğrudan patch yapalım.
    mocker.patch.object(get_settings(), "JWT_SECRET_KEY", "s9nUP5o+IfDZ6+KEVCfuVUDBwHfrD45+9BNJ+C9MUwSW6l15oUuiBqwRps05dIS5RpyY7gzFXdOcJQiUGsWO1w==")
    mocker.patch.object(get_settings(), "ALGORITHM", "HS256")
    mocker.patch.object(get_settings(), "ACCESS_TOKEN_EXPIRE_MINUTES", 60) # Testlerde token süresi

    # supabase.create_client fonksiyonunu mock'la, böylece gerçek bir istemci oluşturulmaz.
    # Bunun yerine, mock'lanmış auth metotlarına sahip sahte bir istemci döner.
    mock_supabase_client = MagicMock()
    mock_supabase_client.auth = MagicMock()
    mock_supabase_client.auth.sign_up = mocker.patch("supabase.Client.auth.sign_up", return_value=mock_sign_up_response)
    mock_supabase_client.auth.sign_in_with_password = mocker.patch("supabase.Client.auth.sign_in_with_password", return_value=mock_sign_in_response)
    mock_supabase_client.auth.sign_out = mocker.patch("supabase.Client.auth.sign_out", return_value=None)
    mock_supabase_client.auth.update_user = mocker.patch("supabase.Client.auth.update_user", return_value=mock_update_user_response)

    mocker.patch("supabase.create_client", return_value=mock_supabase_client)

    # Mock'lanmış supabase istemcisini döndür
    return mock_supabase_client

# JWT oluşturmak için jose kütüphanesini import edin
from jose import jwt