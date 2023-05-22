from collections import Counter

class DataRecorder:
    def __init__(self, filename):
        self.data = Counter()
        self.filename = filename
        self.load_from_file()

    def load_from_file(self):
        try:
            with open(self.filename, 'r') as f:
                for line in f:
                    key, value = line.strip().split('|')
                    self.data[key.strip()] = int(value.strip())
        except FileNotFoundError:
            pass

    def add_data(self, value):
        self.data[str(value)] += 1

    def get_sorted_data(self):
        sorted_data = sorted(self.data.items(), key=lambda x: x[1], reverse=True)
        return sorted_data

    def save_to_file(self):
        sorted_data = self.get_sorted_data()
        with open(self.filename, 'w') as f:
            for item in sorted_data:
                f.write(f"{item[0]} | {item[1]}\n")
