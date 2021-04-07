import json
import config


class Option:
    # Options should be a list of possible options
    def __init__(self, options=[], default=None):
        self.options = options
        self.default = default

    def push(self, item):
        self.options.append(item)

    def pop(self, index=None):
        if index:
            return self.options.pop(index)
        return self.options.pop()

    def save(self):
        amount = len(self.options)
        indexed_options = self._indexed_dict(self.options)
        try:
            with open(config.config_location / 'cache.json', 'a+') as f:
                f.seek(0)
                old_raw = f.read()
                try:
                    old_options = json.loads(old_raw)
                # Probably empty file
                except json.JSONDecodeError as e:
                    print(old_raw)
                    if len(old_raw) == 0:
                        f.write(json.dumps(indexed_options))
                        f.close()
                        return
                    else:
                        raise e

                # Overwrites anything in old that is also in self.options, but anything else is kept
                new_options = dict(list(old_options.items()) +
                                   list(indexed_options.items()))
                # Deletes old content
                f.seek(f.truncate(0))
                # Writes the new cache
                f.write(json.dumps(new_options))
                f.close()

        except OSError as e:
            print(e)
            exit(1)

    def get(self):
        try:
            with open(config.config_location / 'cache.json', 'r') as f:
                cached = json.loads(f.read())
                f.close()
                return cached
        except OSError as e:
            print(e)
            exit(1)

    def find_cached(self, index):
        try:
            with open(config.config_location / 'cache.json', 'r') as f:
                cached = json.loads(f.read())
                return cached[str(index)]
        except OSError as e:
            print(e)
            exit(1)
    # Prints all items, then returns the item chosen

    def print_and_return_answer(self, message=None):
        amount = len(self.options)
        number = -1
        if amount > 0:
            i = 0
            while i <= amount:
                print("{index}:{option}".format(
                    index=str(i), option=self.options[i]))
                i += 1

            if not message:
                message = "Choose one option"
            if self.default:
                message += " [" + default + "]"
            message += " (q to quit): "

            while True:
                try:
                    answer = input(message)
                    if answer == 'q':
                        exit(0)
                    elif self.default and answer == "":
                        number = default
                        break
                    else:
                        answer = int(answer)
                        if answer >= 1 and answer <= amount:
                            number = answer - 1
                            break
                        else:
                            print("Please type a number in range: 1 - {}".format(
                                  str(amount)))
                            continue
                except ValueError:
                    print('Please type a number')
                    continue
        if not number == -1:
            return self.options[number]

    def _indexed_dict(self, array):
        indexed_dict = {}
        if len(array) == 1:
            indexed_dict['0'] = array[0]
        else:
            for i, item in enumerate(array, 1):
                indexed_dict[str(i)] = item
                self.top_index = i
        return indexed_dict
