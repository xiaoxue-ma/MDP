from cache import Cache_Rpi

q = Cache_Rpi()

q.enqueue("1")
print q.is_empty()
print q.dequeue()

print q.is_empty()