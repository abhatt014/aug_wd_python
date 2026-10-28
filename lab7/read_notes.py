try:
    with open("mynotes.txt", "r") as f:
        lines = f.read()
    print(lines)    
except FileNotFoundError:
    print("File not found. Please check the file name and try again.")    