import json

import selido.config as config
from selido.parsing import Tag, Resource
from selido.options import Options

from typing import List
from dataclasses import dataclass, field


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
        if indentation_level >= 3:
            self.indentation_level = indentation_level
        else:
            self.indentation_level = 3
        if space_between_tags >= 3:
            self.space_between_tags = space_between_tags
        else:
            self.space_between_tags = 3
        self.no_columns = no_columns
        self.with_id = with_id

        self.oc = Options()

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
