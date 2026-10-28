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
#############2nd task########################
def analyse_list(num_list):
    if not num_list:
        return "list is empty"
    total_sum = sum(num_list)
    average = total_sum / len(num_list)
    largest = max(num_list)
    smallest = min(num_list)
    
    return {
            "sum":total_sum,
            "average":average,
            "largest":largest,
            "smallest":smallest
            }
 

sample_num = [15,2,8,48,10]
result = analyse_list(sample_num)
print(result)

#############3rd task############################
def greet(name,time_of_day):
    return f"Good{time_of_day}, {name}"

print(greet("Alice","morning"))
print(greet("John","evening"))
print(greet("Bob","Afternoon"))