fname = input("Enter the file name: ")
try:
    with open(fname, "r") as f:
        lines = f.readlines()
    print(f"The number of lines in {fname} is: {len(lines)}")
except FileNotFoundError:
    print("File not found. Please check the file name and try again.")
    