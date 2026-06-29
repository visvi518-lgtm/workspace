from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserProfile

db = SessionLocal()
if not db.query(User).filter(User.email == "admin@test.com").first():
    u = User(
        email="admin@test.com",
        password_hash=get_password_hash("Admin123!"),
        nickname="관리자",
        is_admin=True,
    )
    u.profile = UserProfile()
    db.add(u)
    db.commit()
    print("관리자 계정 생성: admin@test.com / Admin123!")
else:
    print("이미 존재")

if not db.query(User).filter(User.email == "user@test.com").first():
    u2 = User(
        email="user@test.com",
        password_hash=get_password_hash("User1234!"),
        nickname="테스트유저",
    )
    u2.profile = UserProfile(height=170, weight=65, nationality="korean")
    db.add(u2)
    db.commit()
    print("일반 계정 생성: user@test.com / User1234!")

db.close()
