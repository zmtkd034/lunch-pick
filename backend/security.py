"""비밀번호 해시와 세션 값(L25, Task Flow의 같은 모듈을 가져옴). 표준 라이브러리 hashlib.scrypt와 사용자별 salt를 쓴다(새 패키지 없음).

저장 형식: scrypt$n$r$p$salt(16진수)$hash(16진수). 원문 비밀번호는 저장·출력하지 않는다.
세션 값은 쿠키로만 보내고, DB에는 SHA-256 해시만 저장한다.
"""

import hashlib
import hmac
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 16
KEY_BYTES = 32
SESSION_TOKEN_BYTES = 32


def _scrypt(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=KEY_BYTES)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    key = _scrypt(password, salt, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, key_hex = stored.split("$")
        if algorithm != "scrypt":
            return False
        key = _scrypt(password, bytes.fromhex(salt_hex), int(n), int(r), int(p))
    except ValueError:
        return False
    # 비교 시간으로 값이 드러나지 않게 한다.
    return hmac.compare_digest(key, bytes.fromhex(key_hex))


# 없는 아이디로 로그인할 때도 비밀번호 확인과 비슷한 시간이 걸리게 해, 응답 시간으로 아이디 존재 여부가 드러나지 않게 한다.
_DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def verify_dummy_password(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def new_session_token() -> str:
    return secrets.token_urlsafe(SESSION_TOKEN_BYTES)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
