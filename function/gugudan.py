print("구구단 몇단을 계산할까요?")

dan = int(input())   #중요함
print("구구단 ",dan,"단을 계산합니다.")
for i in range(1,10):
    result = dan * i
    print(dan," x ",i," = ",result)  #print(f"{dan} x {i} = {dan * i }"")

