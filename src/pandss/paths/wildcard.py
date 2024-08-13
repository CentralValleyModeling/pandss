from re import compile

WILDCARD_PATTERN_LITERAL = compile(r"\.\*")
WILDCARD_STR = ".*"
WILDCARD_PATTERN = compile(WILDCARD_STR)
