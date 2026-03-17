import random

true_value = random.randint(1,100)
guess_count = 0

print("숫자를 입력하세요(1~100)")
guess_value =9999

while true_value != guess_value:
    guess_value = int(input())
    guess_count +=1
    print(f"{guess_count}")
    
    if (true_value > guess_value):
        print(f"시도횟수 : {guess_count} 더 높은 숫자를 입력하세오")
    elif(true_value < guess_value):
        print(f"시도횟수 : {guess_count} 더 낮은 숫자를 입력하세요")
    else:
        break


print("정답입니다^^")