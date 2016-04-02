class Rpi_Queue():
    def __init__(self):
        self.items = []

    def is_empty(self):
        return self.items == []

    def enqueue(self, item):
        self.items.insert(0,item)

    def peek(self):
        if not self.items == []:
            return self.items[len(self.items) - 1]

    def dequeue(self):
        if not self.items == []:
            return self.items.pop()

    def size(self):
        return len(self.items)


