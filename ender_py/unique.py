with open("ender_py/unique.txt", "r", encoding="utf-8") as f:
    unique_characters = f.read()

print(len(unique_characters))
uniquely_sorted = "".join(sorted(set(unique_characters)))

print(len(uniquely_sorted))

print(uniquely_sorted)

with open("ender_py/unique.txt", "w", encoding="utf-8") as f:
    f.write(uniquely_sorted)
