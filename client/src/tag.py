class Tag:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value

    def __str__(self):
        if self.value:
            return self.key + ":" + self.value
        else:
            return self.key


class Item:
    # Tags is a list of Tags
    def __init__(self, id, tags):
        self.id = id
        self.tags = tags


def items_from_list_of_dict(dict_list, keys_to_ignore=[], sort=False):
    items = []
    for item in dict_list:
        tags = []
        for tag in item['tags']:
            if not tag['key'] in keys_to_ignore:
                if 'value' in tag:
                    tags.append(Tag(tag['key'], tag['value']))
                else:
                    tags.append(Tag(tag['key']))
        items.append(Item(item['id'], tags))
        if sort:
            tags.sort()
    return items


class TagPrinter:
    # Tags should be a list of items, with each list being one set of tags
    def __init__(self, tags, indent_tags=15, space_between_tags=3, with_id=True, key_columns=None):
        self.tags = tags
        self.indent_tags = indent_tags
        if space_between_tags >= 3:
            self.space_between_tags = space_between_tags
        else:
            self.space_between_tags = 3
        self.with_id = with_id
        self.key_columns = key_columns

    def print(self):
        if self.key_columns:
            self.print_with_columns()
        else:
            if self.with_id:
                space = ' ' * 24
                print("ID", "Tags", sep=space)

            for item in self.tags:
                self.print_item(item)

    def print_item(self, item):
        if self.with_id:
            space = ' ' * 2
            print(item.id, end=space)
        for i, tag in enumerate(item.tags):
            if not self.print_too_long(tag):
                space = self.space(tag)
                print(tag, end='')
                if not i == len(item.tags) - 1:
                    print(space, end='')
        print()

    def print_with_columns(self):
        if self.with_id:
            space = ' ' * 24
            print("ID", end=space)

        for col in self.key_columns:
            if not self.print_too_long(col):
                space = self.space(col)
                print(col, end=space)
        print("Other tags\n")

        for item in self.tags:
            self.print_item_columned(item)

    def print_item_columned(self, item):
        # Print columned tags, then rest
        if self.with_id:
            space = ' ' * 2
            print(item.id, end=space)
        for column in self.key_columns:
            printed = False
            for tag in item.tags:
                if tag.key == column:
                    printed = True
                    if tag.value:
                        if not self.print_too_long(tag.value):
                            space = self.space(tag.value)
                            print(tag.value, end=space)
                    else:
                        space = self.space("<>")
                        print("<>", end=space)
            if not printed:
                print('-' + ' ' * (self.indent_tags - 1), end='')
        for i, tag in enumerate(item.tags):
            if tag.key not in self.key_columns:
                print(tag, end='')
                if not i == len(item.tags) - 1:
                    print(',', end='')
        print()

    def space(self, string):
        return ' ' * (self.indent_tags - len(str(string)))

    def print_too_long(self, tag):
        if len(str(tag)) > self.indent_tags - self.space_between_tags:
            space = ' ' * (self.space_between_tags - 2)
            print(str(tag)[0:self.indent_tags - self.space_between_tags] +
                  '..' + space, end='')
            return True
        else:
            return False
