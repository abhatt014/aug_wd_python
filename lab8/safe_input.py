while True:
    try:
        user_input = int(input("Please enter a number: "))
        break
    except ValueError:
        print("Invalid input. Please enter a valid number.")
print(f"you entered: {user_input}")        