import helper_functions

print(f"value of __name__ is: {__name__}") 
if __name__ == "__main__":
    message = helper_functions.greet("Bob")
    print(message)
    sum_result = helper_functions.add(7, 3)
    print(f"From main_app, the sum is: {sum_result}")