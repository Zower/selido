class OptionChooser:
    # Options should be a list of possible options
    def __init__(self, options, default=None):
        self.options = options
        self.amount = len(self.options)
        self.default = default
        self.number = -1

    def get_answer(self, message=None):
        if self.amount == len(self.options) and len(self.options) > 0:
            for i, option in enumerate(self.options, 1):
                print(str(i) + ":", option)

            prompt = ""
            if not message:
                message = "Choose one option "
            if self.default:
                message += "[" + default + "]:"
            message += "(q to quit): "

            while True:
                try:
                    answer = input(message)
                    if answer == 'q':
                        exit(0)
                    elif self.default and answer == "":
                        self.number = default
                        break
                    else:
                        answer = int(answer)
                        if answer >= 1 and answer <= self.amount:
                            self.number = answer - 1
                            break
                        else:
                            print("Please type a number in range: 1 - " +
                                  str(self.amount))
                            continue
                except ValueError:
                    print('Please type a number')
                    continue
        return self.options[self.number]
