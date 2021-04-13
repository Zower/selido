import json
import selido.config as config

from typing import List
from dataclasses import dataclass, field


@dataclass
class Tag:
    key: str
    value: str = None

    def __str__(self):
        if self.value:
            return self.key + ":" + self.value
        else:
            return self.key


@dataclass
class Resource:
    id: str  # ID as returned from the server
    tags: List[Tag]  # Tags associated with this ID, a list of type "Tag"


@dataclass
class TagPrinter:
    resources: List[Resource]  # The resources to print
    key_columns: List[str]  # Keys that will have their own columns
    indentation_level: int  # Indentation level between tags
    space_between_tags: int  # Minimum space between tags
    no_columns: bool   # Only print tags, no columns, indices, ids, or anything else. key_columns still get printed for each item, but there is no top level identifier showing what the column was
    with_id: bool  # Print IDs

    def __init__(self, resources, key_columns=None, indentation_level=15, space_between_tags=3, no_columns=False, with_id=False):
        self.resources = resources
        self.key_columns = key_columns
        self.indentation_level = indentation_level
        if space_between_tags >= 3:
            self.space_between_tags = space_between_tags
        else:
            self.space_between_tags = 3
        self.no_columns = no_columns
        self.with_id = with_id

        self.oc = Option()

    def print(self):
        # Calculate length of string of the number of indices
        max_index_length = len(str(len(self.resources)))

        self._print_columns(max_index_length)

        self._print_items(max_index_length)

    def count(self):
        print("# of resources: {}".format(len(self.resources)))

    def mcount(self):
        print(len(self.resources))

    def _print_columns(self, max_index_length):
        # Columns should be printed
        if not self.no_columns:

            # If the max is less than length of the word 'index', then just one space is needed
            if max_index_length <= 5:
                index_space = ' '
            # Else, the space must be max_index_length minus 5 (for the word 'index'), plus one for spacing.
            else:
                index_space = ' ' * (max_index_length - 4)

            # Printed whether columned or not
            print("Index", end=index_space)

            if self.with_id:
                print("ID", end=' ' * 24)

            # No key columns
            if not self.key_columns:
                print("Tags")
            # This is a custom column print, so print those
            else:
                for col in self.key_columns:
                    if not self.print_too_long(col):
                        space = self.space(col)
                        print(col, end=space)
                print("Other tags")

    def _print_items(self, max_index_length):
        # Set the print_item function to be used, to avoid multiple if checks for every item
        if self.key_columns:
            item_function = self._print_item_columned
        else:
            item_function = self._print_item

        # Only one thing to print, therefore index should be 0
        if len(self.resources) == 1:
            # Push the id to OC, so it can be saved later
            self.oc.push(self.resources[0].id)
            # Print index
            print('0', end=' ' * 5)

            # Call _print_item or _print_item_columned
            item_function(self.resources[0])

        # More than 1 resource, print from index 1
        else:
            self._print_multiple(item_function, max_index_length)

        # Save the options to file
        self.oc.save()

    def _print_multiple(self, item_function, max_index_length):
        for i, item in enumerate(self.resources, 1):
            # Push the id to OC, so it can be saved later
            self.oc.push(item.id)

            # Length of string of index
            tag_length = len(str(i))
            # Check if extra spaces must be added, or not
            if tag_length <= 5:
                tag_space = ' ' * (6 - tag_length)
            else:
                tag_space = ' ' * (max_index_length - tag_length + 1)

            # Print index
            print(i, end=tag_space)

            # Call _print_item or _print_item_columned
            item_function(item)

    def _print_item(self, item):
        # Print ID
        if self.with_id:
            space = ' ' * 2
            print(item.id, end=space)

        for i, tag in enumerate(item.tags):
            if not self.print_too_long(tag):
                # Calculate necessary space for tag
                space = self.space(tag)
                # Print the tag
                print(tag, end='')
                if not i == len(item.tags) - 1:
                    print(space, end='')

        # New line
        print()

    def _print_item_columned(self, item):
        # Print ID
        if self.with_id:
            space = ' ' * 2
            print(item.id, end=space)

        # Print columned values first
        for column in self.key_columns:
            printed = False
            for tag in item.tags:
                # If the key matches a column
                if tag.key == column:
                    printed = True
                    # Print the value
                    if tag.value:
                        if not self.print_too_long(tag.value):
                            space = self.space(tag.value)
                            print(tag.value, end=space)
                    # If no value, print <> to indicate that the key is there
                    else:
                        space = self.space("<>")
                        print("<>", end=space)
            # The item does not have the specified key, print -
            if not printed:
                print('-' + ' ' * (self.indentation_level - 1), end='')

        # Print rest of the tags
        for tag in item.tags:
            if tag.key not in self.key_columns:
                if not self.print_too_long(tag):
                    space = self.space(tag)
                    print(tag, end=space)
        # New line
        print()

    # Calculate necessary space for a given string
    def space(self, string):
        return ' ' * (self.indentation_level - len(str(string)))

    # Prints the string sliced if it is too long, otherwise returns false
    def print_too_long(self, tag):
        if len(str(tag)) > self.indentation_level - self.space_between_tags:
            space = ' ' * (self.space_between_tags - 2)
            print(str(tag)[0:self.indentation_level - self.space_between_tags] +
                  '..' + space, end='')
            return True
        else:
            return False


# Options printing and saving
@dataclass
class Option:
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
            while i <= amount:
                print("{index}:{option}".format(
                    index=str(i), option=self.options[i]))
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


# Creates Resource types from a list of dictionaries, with each dictionary being one resource in the format returned from server, e.g. {'id': '2309f001FA0023123', 'tags': [{'key': 'test', 'value':'true'}]}


def resources_from_list_of_dict(dict_list, keys_to_ignore=[], sort=False):
    items = []
    for item in dict_list:
        tags = []
        for tag in item['tags']:
            if not tag['key'] in keys_to_ignore:
                if 'value' in tag:
                    tags.append(Tag(tag['key'], tag['value']))
                else:
                    tags.append(Tag(tag['key']))
        items.append(Resource(item['id'], tags))
        if sort:
            # Forcing sort to use string representation of tag
            tags.sort(key=lambda x: str(x))
    return items
