from faker import Faker
fake = Faker()  # Create a Faker generator
for i in range(10):
    print(f"Fake Name: {fake.name()}")
    print(f"Fake Address: {fake.address()}")
    print(f"Fake Text: {fake.text()}")
    print("==================================================")
