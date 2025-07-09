import re
from typing import Optional, Any, Pattern
from .triggers import load_triggers
from .process import Node, ArrowStyle, ParsedRoute

# variable names or commands used in flow transitions
_TOKEN_RE = re.compile(r"""
    ^                  # start of string
    /?                 # optional leading slash
    [A-Za-z_]\w*       # identifier starting with letter or underscore
    (?:\([^)]*\))?     # optional (...) group with no nesting
    $                  # end of string
""", re.VERBOSE)

def get_token_list(input_string: str, separator: str) -> list[str]:
    """
    Tokenize a string by splitting on a top-level separator, while preserving
    any separator characters that appear within parentheses.

    This function returns a list of non-empty tokens, each trimmed of
    leading and trailing whitespace. Parenthesized substrings are never
    split—even if they contain the separator.

    Example:
        >>> get_token_list("foo,bar(baz,qux),zap", ",")
        ["foo", "bar(baz,qux)", "zap"]
    """
    split_parts: list[str] = []
    current_chars: list[str] = []
    parenthesis_depth: int = 0

    for character in input_string:
        
        if character == "(":
            parenthesis_depth += 1
        elif character == ")":
            parenthesis_depth = max(0, parenthesis_depth - 1)

        if character == separator and parenthesis_depth == 0:
            split_parts.append("".join(current_chars))
            current_chars = []
        else:
            current_chars.append(character)

    split_parts.append("".join(current_chars))

    return [part.strip() for part in split_parts if part.strip()]


class Flow:
    
    def __init__(self, triggers_file: Optional[str] = None):
        self.triggers_file = triggers_file
        self.in_use: bool = False
        self.arrows: set[ArrowStyle] = set()
        
        self._regex_ready: bool = False
        self._regex_patterns: list[tuple[Pattern, ArrowStyle, str]] = []
    
    def activate(self):
        self.in_use = True
        return self

    def deactivate(self):
        self.in_use = False
        return self

    def add_arrow_style(self,
                        stem: str,
                        brackets: tuple[str, str],
                        separator: str,
                        tip: str
                        ):
        style = ArrowStyle(
            stem=stem,
            brackets=brackets,
            separator=separator,
            tip=tip
            )
        self.arrows.add(style)
        self._regex_ready = False
        self._regex_patterns.clear()

    def triggers(self, json_dict: Optional[dict[str, Any]] = None):
        if json_dict is None: 
            if self.triggers_file is None:
                # use the file TRIGGERS
                return load_triggers()
            else:
                return load_triggers(triggers_file=self.triggers_file)
        else:
            return load_triggers(json_dict=json_dict)

    def _build_labeled_complete(self, base, left_bracket, right_bracket, tip) -> Pattern:
        left  = rf"{base}{left_bracket}"
        right = rf"{right_bracket}{base}{tip}"
        regex = rf"""
            ^\s*
            (?P<source>.+?)\s*{left}\s*
            (?P<label>.*?)\s*{right}\s*
            (?P<target>.+?)\s*$
        """
        return re.compile(regex, re.VERBOSE)

    def _build_unlabeled_complete(self, base, tip) -> Pattern:
        arrow  = rf"{base}{tip}"
        regex = rf"""
            ^\s*
            (?P<source>.+?)\s*{arrow}\s*
            (?P<target>.+?)\s*$
        """
        return re.compile(regex, re.VERBOSE)
    
    def _build_labeled_dangling_right(self, base, left_bracket, right_bracket, tip) -> Pattern:
        left  = rf"{base}{left_bracket}"
        right = rf"{right_bracket}{base}{tip}"
        regex = rf"""
            ^\s*
            (?P<source>.+?)\s*{left}\s*
            (?P<label>.*?)\s*{right}\s*$
        """
        return re.compile(regex, re.VERBOSE)

    def _build_unlabeled_dangling_right(self, base, tip) -> Pattern:
        arrow  = rf"{base}{tip}"
        regex = rf"""
            ^\s*
            (?P<source>.+?)\s*{arrow}\s*$
        """
        return re.compile(regex, re.VERBOSE)
    
    def _build_labeled_dangling_left(self, base, left_bracket, right_bracket, tip) -> Pattern:
        left  = rf"{base}{left_bracket}"
        right = rf"{right_bracket}{base}{tip}"
        regex = rf"""
            ^\s*
            {left}\s*
            (?P<label>.*?)\s*{right}\s*
            (?P<target>.+?)\s*$
        """
        return re.compile(regex, re.VERBOSE)

    def _build_unlabeled_dangling_left(self, base, tip) -> Pattern:
        arrow = rf"{base}{tip}"
        regex = rf"""
            ^\s*
            {arrow}\s*
            (?P<target>.+?)\s*$
        """
        return re.compile(regex, re.VERBOSE)


    def _unpack_labeled_complete(self, matched_pattern: re.Match) -> tuple[str,str,str]:
        return matched_pattern.group("source"), matched_pattern.group("label"), matched_pattern.group("target")

    def _unpack_unlabeled_complete(self, matched_pattern: re.Match) -> tuple[str,str,str]:
        return matched_pattern.group("source"), "", matched_pattern.group("target")
    
    def _unpack_labeled_dangling_right(self, matched_pattern: re.Match) -> tuple[str,str,str]:
        return matched_pattern.group("source"), matched_pattern.group("label"), ""
    
    def _unpack_unlabeled_dangling_right(self, matched_pattern: re.Match) -> tuple[str,str,str]:
        return matched_pattern.group("source"), "", ""
    
    def _unpack_labeled_dangling_left(self, matched_pattern: re.Match) -> tuple[str,str,str]:
        return "", matched_pattern.group("label"), matched_pattern.group("target")

    def _unpack_unlabeled_dangling_left(self, matched_pattern: re.Match) -> tuple[str,str,str]:
        return "", "", matched_pattern.group("target")

    def _prepare_regex(self):
        if self._regex_ready:
            return

        for style in self.arrows:
            base   = re.escape(style.stem * 2)
            left_bracket, right_bracket = map(re.escape, style.brackets)
            tip    = re.escape(style.tip)

            # labeled
            pattern_complex_complete = self._build_labeled_complete(base, left_bracket, right_bracket, tip)
            self._regex_patterns.append((pattern_complex_complete, style, self._unpack_labeled_complete))

            pattern_complex_dangling_left = self._build_labeled_dangling_left(base, left_bracket, right_bracket, tip)
            self._regex_patterns.append((pattern_complex_dangling_left, style, self._unpack_labeled_dangling_left))

            pattern_complex_dangling = self._build_labeled_dangling_right(base, left_bracket, right_bracket, tip)
            self._regex_patterns.append((pattern_complex_dangling, style, self._unpack_labeled_dangling_right))

            # unlabeld
            pattern_simple_complete = self._build_unlabeled_complete(base, tip)
            self._regex_patterns.append((pattern_simple_complete, style, self._unpack_unlabeled_complete))

            pattern_simple_dangling = self._build_unlabeled_dangling_left(base, tip)
            self._regex_patterns.append((pattern_simple_dangling, style, self._unpack_unlabeled_dangling_left))

            pattern_simple_dangling_left = self._build_unlabeled_dangling_right(base, tip)
            self._regex_patterns.append((pattern_simple_dangling_left, style, self._unpack_unlabeled_dangling_right))

        self._regex_ready = True

    def _validate_tokens(self, tokens: list[str], text: str):
        for token in tokens:
            if not _TOKEN_RE.match(token):
                raise ValueError(f"Invalid token {token!r} in route {text!r}")

    def _parse_standalone(self, text: str) -> ParsedRoute:
        # split on commas, strip whitespace, drop empties
        source_list = get_token_list(text, separator=',')
        # validate each token
        self._validate_tokens(source_list, text)
        return ParsedRoute(
            source=tuple(Node(tok) for tok in source_list),
            label=(),
            target=(),
            style=None
    )

    def ready(self):
        if self.in_use:
            self._prepare_regex()

    def parse_route(self, route: str) -> ParsedRoute:
        route = route.strip()
        if not self._regex_ready:
            self._prepare_regex()
        
        for pattern, style, unpack in self._regex_patterns:
            matched_pattern = pattern.match(route)
            if not matched_pattern:
                continue
            source_raw_text, label_raw_text, target_raw_text = unpack(matched_pattern)

            source_list = get_token_list(source_raw_text, style.separator)
            label_list = get_token_list(label_raw_text, style.separator)
            target_list = get_token_list(target_raw_text, style.separator)
            self._validate_tokens(source_list + label_list + target_list, route)

            return ParsedRoute(
                source=tuple(Node(tok) for tok in source_list),
                label=tuple(Node(tok) for tok in label_list),
                target=tuple(Node(tok) for tok in target_list),
                style=style,
            )
        
        return self._parse_standalone(route)

    def parse_routes(self, routes: list[str]) -> list[ParsedRoute]:
        return [self.parse_route(route=route) for route in routes]

                


