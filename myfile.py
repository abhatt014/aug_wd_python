# f = open('data.txt', 'r')
# content = f.read()  # Reads the whole file into a string
# print("--- Entire Content ---")
# print(content)
# f.close()  # Always close the file
# f = open('data.txt', 'r')
# for line in f:  # Files are iterable objects, like lists
#     print(line.strip())  # .strip() removes \n
# f.close()


# f = open('data.txt', 'r')
# first_line = f.readline() # Reads the first line
# print(first_line.strip())
# second_line = f.readline() # Reads the next line
# if second_line:
#     print(second_line.strip())
# f.close()


# f = open('output.txt', 'w')  # 'w' overwrites or creates
# f.write("This is the first line!\n")
# f.write("This is another line.\n")
# print("Data written to output.txt")
# f.close()


# f = open('output.txt', 'a')
# f.write("This line will be appended as 3rd line\n")
# print("Data appended to output.txt")
# f.close()


# Reading with 'with'

# with open('data.txt', 'r') as f:
#     content = f.read()
#     print(content)


# Writing with 'with'

with open('output_with.txt', 'w') as f:
    f.write("Hello from the 'with' statement.\n")
    f.write("This file will auto-close.\n")

print("Data written to output_with.txt")

