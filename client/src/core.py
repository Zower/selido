import json
import config


class Resource:
    # Tags is a list of type Tag
    def __init__(self, id, tags):
        self.id = id
        self.tags = tags


class Tag:
    def __init__(self, key, value=None):
        self.key = key
        self.value = value

    def __str__(self):
        if self.value:
            return self.key + ":" + self.value
        else:
            return self.key


class TagPrinter:
    # Tags should be a list of items, with each list being one set of tags
    def __init__(self, tags, indent_tags=15, space_between_tags=3, with_id=True, key_columns=None, count=False, mcount=False):
        self.tags = tags
        self.indent_tags = indent_tags
        if space_between_tags >= 3:
            self.space_between_tags = space_between_tags
        else:
            self.space_between_tags = 3
        self.with_id = with_id
        self.key_columns = key_columns
        self.oc = Option()
        self.count = count
        self.mcount = mcount

    def print(self):
        if self.mcount:
            print(len(self.tags))
        elif self.key_columns:
            self.print_with_columns()
        # Print regular
        else:
            # This means there are more indexes than available space so indent some more
            if len(self.tags) > 10000:
                i_space = ' ' * (len('1000') - 4)
                print("Index", end=i_space)
                t_space = ' '
            # 5 spaces is enough
            else:
                t_space = ' ' * 5
                print("Index", end=' ')
            if self.with_id:
                print("ID", "Tags", sep=' ' * 24)

            if len(self.tags) == 1:
                self.oc.push(self.tags[0].id)
                print('0', end='     ')
                self.print_item(self.tags[0])
            else:
                for i, item in enumerate(self.tags, 1):
                    self.oc.push(item.id)
                    print(i, end=t_space)
                    self.print_item(item)
            self.oc.save()
        if self.count: 
            print("# of results: {}".format(len(self.tags)))
    
    def print_with_columns(self):

        # This means there are more indexes than available space so indent some more
        if len(self.tags) > 10000:
            i_space = ' ' * (len('1000') - 4)
            print("Index", end=i_space)
            t_space = ' '
        # 5 spaces is enough
        else:
            t_space = ' ' * 5
            print("Index", end=' ')
        if self.with_id:
            print("ID", end=' ' * 24)

        for col in self.key_columns:
            if not self.print_too_long(col):
                space = self.space(col)
                print(col, end=space)
        print("Other tags\n")

        if len(self.tags) == 1:
            self.oc.push(self.tags[0].id)
            print('0', end='     ')
            self.print_item_columned(self.tags[0])
        else:
            for i, item in enumerate(self.tags, 1):
                self.oc.push(item.id)
                print(i, end='     ')
                self.print_item_columned(item)
        self.oc.save()

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


# Options printing and saving

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


class Body:
    def __init__(self, limbs={}):
        self.limbs = limbs

    def get(self):
        return self.limbs

    def add(self, name, value):
        self.limbs[name] = value

    def remove(self, name):
        return self.limbs.pop(name)
