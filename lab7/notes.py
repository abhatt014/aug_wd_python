import datetime
note = input("enter a short note:  ")
curr_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
with open("mynotes.txt", "a") as f:
    f.write(f"[{curr_time}] {note}\n")
print("Note saved successfully.")