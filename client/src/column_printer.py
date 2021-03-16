class ColumnPrinter:
    def __init__(self, indent, columns, tags):
        self.indent = indent
        self.columns = columns

    def print(self):
        # if len(object['name']) > indent - 5:
        #     print(object['name'][0:indent - 5] + '..   ', end='')
        # else:
        #     indent_length = indent - len(object['name'])
        #     print(object['name'] + ' ' * indent_length, end='')
        for column in self.columns:
            if len(column) > self.indent - 5:
                print(column[0:self.indent - 5] + '..   ' + 's')
            else:
                space = ' ' * (self.indent - len(column))
                print(column + space + 's')
