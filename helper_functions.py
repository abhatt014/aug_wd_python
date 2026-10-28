def greet(name):
 return f"Hello, {name} from my_helper_functions!"
def add(a, b):
 return a + b
print(f"value of __name__ is: {__name__}") 

if __name__ == "__main__":
    print("my_helper_functions.py is being run directly!")
    user_name = input("Enter your name: ")
    print(greet(user_name))
    result = add(10, 5)
    print(f"The sum of 10 and 5 is: {result}")
