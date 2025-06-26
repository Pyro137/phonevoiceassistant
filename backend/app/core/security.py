

from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Verilen şifreyi bcrypt kullanarak hash'ler.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Düz metin şifreyi (plain_password) hashlenmiş şifre (hashed_password) ile karşılaştırır.
    Eğer eşleşirlerse True, aksi takdirde False döner.
    """
    return pwd_context.verify(plain_password, hashed_password)
