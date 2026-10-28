import math
import random
from faker import Faker

if __name__ == "__main__":
    fake = Faker()
    for i in range(1,6):
        print(f"Profile{i}:")
        print(f"Name: {fake.name()}")
        print(f"Name: {fake.email()}")
        print(f"Name: {fake.job()}")
        print("=" * 30)

    # secret_num = random.randint(1,100)
    # guess = None
    # while guess != secret_num:
    #     guess = int(input("guess the secret number between 1 and 100:  "))
    #     if guess > secret_num:
    #         print("Too High")
    #     elif guess < secret_num:
    #         print("Too Low")
    #     else:
    #         print("Congratulations!! you have guessed it")         
    # user_input = int(input("enter the number :  "))
    # print(f"Square Root of {user_input} : {math.sqrt(user_input)}")
    # print(f"Factorial of {user_input} : {math.factorial(user_input)}")