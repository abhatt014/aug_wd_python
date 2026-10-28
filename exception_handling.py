try:    
    a = 10
    num = int(input("Enter a number to divide by: "))
    c = a / num      
    print(f"Result: {c}")

except ValueError:
    print("Invalid input! Please enter a valid integer.")
# except ZeroDivisionError:
#     print("Error: Division by zero is not allowed.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    print("Execution completed.")        