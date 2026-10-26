def add(a,b):
	return a+b
def subtract(a,b):
	return a-b
def multiply(a,b):
	return a*b
def divide(a,b):
	if b == 0:
		return "Error: cannot divide by zero"	
	return a/b	

num1=float(input("enter first number:  "))
num2=float(input("enter second number:  ")) 
operation = input("enter the operation (+, -, *, /):  ")

if operation == "+":
	result = add(num1,num2)
if operation == "-":
	result = subtract(num1,num2)
if operation == "*":
	result = multiply(num1,num2)
if operation == "/":
	result = divide(num1,num2)

print(f"Result: {result}")	


