import json

from typing import List
from dataclasses import dataclass, field

import selido.config as config


@dataclass  # Options printing and saving
class Options:
    options: List[str] = field(default_factory=list)

    # Add an option
    def push(self, item):
        self.options.append(item)

    # Remove an option
    def pop(self, index=None):
        if index:
            return self.options.pop(index)
        return self.options.pop()

    # Saves all current options to cache.json in current config location.
    def save(self):
        indexed_options = self._options_indexed_dict()
        try:
            # Need to open in append mode as r+ will not create the file if it does not exist, a+ will.
            with open(config.CONFIG_LOCATION / 'cache.json', 'a+') as f:
                # Seek to start of file, as append('a+') opens at the end.
                f.seek(0)
                old_raw = f.read()
                try:
                    # Load content into dict
                    old_options = json.loads(old_raw)
                # File was probably empty
                except json.JSONDecodeError as e:
                    if len(old_raw) == 0:
                        # Write cache straight to file
                        f.write(json.dumps(indexed_options))
                        f.close()
                        return
                    # Something else went wrong instead
                    else:
                        raise e

                # Overwrites anything in old that is also in new, but anything else is kept
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
        cached = self._get_cached()
        return cached

    # Find the value(ID) stored at key
    def find_cached(self, key):
        cached = self._get_cached()
        return cached[str(key)]

    # Prints all options, then returns the item chosen
    def print_and_return_answer(self, message=None, default=None):
        amount = len(self.options)
        number = -1
        if amount > 0:
            i = 0
            while i < amount:
                print("{index}:{option}".format(
                    index=str(i + 1), option=self.options[i]))
                i += 1

            if not message:
                message = "Choose one option"
            if default:
                message += " [" + default + "]"
            message += " (q to quit): "

            while True:
                try:
                    answer = input(message)
                    if answer == 'q':
                        exit(0)
                    elif default and answer == "":
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

    # Makes an dictionary with an index as a key, e.g. {"1":bar, "0": foo}, or in the case of IDs: {"0": "606ee90d1bbc7f0adad1ef19", "1": "606ee9231bbc7f0adad1ef1a"}
    def _options_indexed_dict(self):
        indexed_dict = {}
        if len(self.options) == 1:
            indexed_dict['0'] = self.options[0]
        else:
            for i, item in enumerate(self.options, 1):
                indexed_dict[str(i)] = item
                self.top_index = i
        return indexed_dict

    # Opens cache.json and returns the contents as given by json.loads()
    def _get_cached(self):
        try:
            with open(config.CONFIG_LOCATION / 'cache.json', 'r') as f:
                cached = json.loads(f.read())
                f.close()
                return cached
        except OSError as e:
            print(e)
            exit(1)
