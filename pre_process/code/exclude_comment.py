from enum import Enum
from io import StringIO
import tokenize

class State(Enum):
    CODE = 1
    C_COMMENT = 2
    CPP_COMMENT = 3
    STRING_SINGLE_LITERAL = 4
    STRING_DUBLE_LITERAL = 5

def exclude_comment(text, ext):
    if ext == 'java' or ext == 'cpp' or ext== 'hpp' or ext == 'cxx' or ext== 'hxx' or ext == 'c' or ext == 'h':
        result = []
        prev = ''
        state = State.CODE
        escape_cnt = 0

        for ch in text:
            # Skip to the end of C-style comment
            if state == State.C_COMMENT:
                if escape_cnt % 2 == 0 and prev == '*' and ch == '/':
                    state = State.CODE
                    escape_cnt = 0
                    prev = ''
                    continue
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                if ch == '\n':
                    # result.append('\n')
                    prev = ''
                else:
                    prev = ch
                continue

            # Skip to the end of the line (C++ style comment)
            if state == State.CPP_COMMENT:
                if ch == '\n':  # End comment
                    state = State.CODE
                    result.append('\n')
                    prev = ''
                continue

            # Skip to the end of the string literal
            #\\エスケープ文字の数を数えて奇数，偶数で対応を返る必要性がある
            if state == State.STRING_DUBLE_LITERAL:
                if escape_cnt % 2 == 0 and ch == '"':
                    state = State.CODE
                    escape_cnt = 0
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                # print(prev)
                result.append(prev)
                prev = ch
                continue
            
             # Skip to the end of the string literal
            if state == State.STRING_SINGLE_LITERAL:
                if escape_cnt % 2 == 0 and ch == '\'':
                    state = State.CODE
                    escape_cnt = 0
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                # print(prev)
                result.append(prev)
                prev = ch
                continue
            
            if ch == '\\':
                escape_cnt += 1
            else:
                escape_cnt = 0
            # Starts C-style comment?
            if escape_cnt % 2 == 0 and prev == '/' and ch == '*':
                state = State.C_COMMENT
                prev = ''
                escape_cnt = 0
                continue

            # Starts C++ style comment?
            if escape_cnt % 2 == 0 and prev == '/' and ch == '/':
                state = State.CPP_COMMENT
                prev = ''
                escape_cnt = 0
                continue

            # Comment has not started yet
            if prev: result.append(prev)

            # Starts string literal?
            if escape_cnt % 2 == 0 and ch == '\'':
                state = State.STRING_SINGLE_LITERAL
                escape_cnt = 0
            
            # Starts string literal?
            if escape_cnt % 2 == 0 and ch == '"':
                state = State.STRING_DUBLE_LITERAL
                escape_cnt = 0
            prev = ch

        # Returns filtered text
        if prev: result.append(prev)
        return ''.join(result)
    
    elif ext == 'py':
        """
        Returns 'source' minus comments and docstrings.
        """
        io_obj = StringIO(text)
        out = ""
        prev_toktype = tokenize.INDENT
        last_lineno = -1
        last_col = 0
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            ltext = tok[4]
            #インデントなどの位置調整
            #１つ前のトークンと比較して行が変わっているか
            if start_line > last_lineno:
                last_col = 0
            #１つ前のトークンとの位置の差を空白で埋める
            if start_col > last_col:
                out += (" " * (start_col - last_col))
            # Remove comments:
            if token_type == tokenize.COMMENT:
                pass
            # This series of conditionals removes docstrings:
            elif token_type == tokenize.STRING:
                
                if prev_toktype != tokenize.INDENT and prev_toktype != tokenize.NEWLINE and start_col > 0:
                    out += token_string
                    
                    # prev_toktype != tokenize.INDENT mean
                    # ークンタイプがSTRINGの前にトークンタイプがINDENTだとドックストリング
                    
                    # prev_toktype != tokenize.NEWLINE mean
                    # NEWLINEとNLの違い
                    # Note regarding NEWLINE vs NL: The tokenize module
                    # differentiates between newlines that start a new statement
                    # and newlines inside of operators such as parens（）〇括弧, brackes[]各括弧,
                    # and curly braces｛｝波括弧.  Newlines inside of operators are
                    # NEWLINE and newlines that start new code are NL.
                    # Catch whole-module docstrings:

                    # star_col > 0 mean
                    # Unlabelled indentation means we're inside an operator
                    
                    # Note regarding the INDENT token: The tokenize module does
                    # not label indentation inside of an operator (parens,
                    # brackets, and curly braces) as actual indentation.
                    # For example:
                    # def foo():
                    #     "The spaces before this docstring are tokenize.INDENT"
                    #     test = [
                    #         "The spaces before this string do not get a token"
                    #     ]
                    # else:
                    #     out += '\n'

            else:
                out += token_string
            prev_toktype = token_type
            last_col = end_col
            last_lineno = end_line
    return out