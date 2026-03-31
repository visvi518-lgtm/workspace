print("당신이 태어난 년도를 입력하세요")
birth = int(input())
myage = 2026 - birth +1
if myage<26 and myage>=20: school ="대학생"
elif myage<19 and myage>=17:school = "고등학생"
elif myage<16 and myage>=1: school = "중학생"
elif myage<13 and myage>=8: school = "초등학생"
else: school = "학생이 아닙니다"
print(school)
