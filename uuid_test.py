import uuid

array = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

r_id = str(uuid.uuid4()).replace("-", '')
buffer = []
for i in range(5):
    start = i * 4
    end = i * 4 + 4
    val = int(r_id[start:end], 16)
    buffer.append(array[val % len(array)])

final_id = "".join(buffer)

print(final_id)
