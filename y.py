import json

with open("lazy.txt", "r") as f:
    data = f.read()

new = {}
new_two = []
data = data.split("\n")
for i in data:
    name, id, color = i.replace('"', "").split(", ")
    new.update({name.lower():color})
    new_two.append({"expected":name.lower(), "return":color})


with open("color.json", "w") as f:
    json.dump(new, f)