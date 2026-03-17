print("본프로그램은 섭씨를 화씨로 변환해주는 프로그램입니다.")
print("변환하고싶은 섭씨 온도를 입력해주세요: ")
temp_c = float(input())
print(f'섭씨온도 : {temp_c:.2f}')
temp_f = ((9/5)*temp_c) +32
print(f'화씨온도 : {temp_f:.2f}')