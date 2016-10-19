def from_byte(N):
    return lambda buf: buf[N:]


def to_byte(N):
    return lambda buf: buf[N:]


to_char = to_byte
from_chars = from_byte


def to_line(N):
    return lambda buf: "\n".join(buf.split("\n")[:N])


def from_line(N):
    return lambda buf: "\n".join(buf.split("\n")[N:])


def from_line_to_line(from_, to_):
    return lambda buf: "\n".join(buf.split("\n")[from_:to_])


def from_byte_to_byte(from_, to_):
    return lambda buf: buf[from_:to_]


def replace_escaped_nl():
    return lambda buf: buf.replace("\\n", "\n")


def strip_nl():
    return lambda buf: buf.replace("\n", "")
