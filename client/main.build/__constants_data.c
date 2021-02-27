
#define INCBIN_PREFIX
#define INCBIN_STYLE INCBIN_STYLE_SNAKE
#define INCBIN_LOCAL

#include "nuitka/incbin.h"

INCBIN(constant_bin, "__constants.bin");

unsigned char const *getConstantsBlobData() {
    return constant_bin_data;
}
