fname = input("Enter the file name: ")
try:
    with open(fname, "r") as f:
        lines = f.read()
    print(lines)
except FileNotFoundError:
    print("File not found. Please check the file name and try again.")  
except Exception as e:
    print(f"An error occurred: {e}")    
finally:
    print("Execution completed.")        