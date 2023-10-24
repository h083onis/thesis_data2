from enum import Enum
import ast
import astor

class State(Enum):
    CODE = 1
    C_COMMENT = 2
    CPP_COMMENT = 3
    PYTHON_LINE_COMMENT = 5
    PYTHON_MULTI_COMMENT_DUBBLE = 6
    STRING_SINGLE_LITERAL = 7
    STRING_DUBLE_LITERAL = 8
    STRING_LITERAL_OR_COMMENT = 9

def exclude_comment(text, ext):
    if ext == 'java' or ext == 'cpp' or ext== 'hpp' or ext == 'c' or ext == 'h':
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
        try:
            parsed_code = ast.parse(text)
            rebuilt_source_code = "\n".join(astor.to_source(parsed_code).splitlines())
        except SyntaxError:
            return False
        
        result = []  # filtered text (char array)
        prev = ''  # previous char
        pprev = ''  # previous previous char
        state = State.CODE
        escape_cnt = 0

        for ch in rebuilt_source_code:
            # Skip to the end of Python-doc-style comment
            if state == State.PYTHON_MULTI_COMMENT_DUBBLE:
                if escape_cnt % 2 == 0 and pprev == '"' and prev == '"' and ch == '"':
                    state = State.CODE
                    pprev = prev = ''
                    escape_cnt = 0
                    continue
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                if ch == '\n':
                    # result.append('\n')
                    pprev = prev = ''
                else:
                    pprev, prev = prev, ch
                continue

            # Skip to the end of the line (Python style comment)
            if state == State.PYTHON_LINE_COMMENT:
                if ch == '\n':  # End comment
                    state = State.CODE
                    result.append('\n')
                    pprev = prev = ''
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
                result.append(prev)
                pprev, prev = prev, ch
                continue
            
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
                pprev, prev = prev, ch
                # print(ch)
                continue
            
            # Starts comment?
            if escape_cnt % 2 == 0 and ch == '#':
                state = State.PYTHON_LINE_COMMENT
                pprev = prev = ''
                escape_cnt = 0
                continue
            
            # STRING_LITERAL OR COMMENT?
            if state == State.STRING_LITERAL_OR_COMMENT:
                if escape_cnt % 2 == 0 and pprev == '"' and prev == '"' and ch == '"':
                    state = State.PYTHON_MULTI_COMMENT_DUBBLE
                    pprev = prev = ''
                    escape_cnt = 0
                elif escape_cnt % 2 == 0 and ch != '"':
                    state = State.STRING_DUBLE_LITERAL
                    result.extend([pprev,prev])
                    escape_cnt = 0
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                pprev, prev = prev, ch
                continue
            
            if ch == '\\':
                escape_cnt += 1
            else:
                escape_cnt = 0
            
            # Starts string literal or Comment?
            if escape_cnt % 2 == 0 and ch == '"':
                state = State.STRING_LITERAL_OR_COMMENT
                pprev, prev = prev, ch
                escape_cnt = 0
                continue
                
            # Starts string literal?
            if escape_cnt % 2 == 0 and ch == "'":
                state = State.STRING_SINGLE_LITERAL
                escape_cnt = 0

            # Comment has not started yet
            if prev: result.append(prev)
            pprev, prev = prev, ch

        # Returns filtered text
        if prev: result.append(prev)
        return ''.join(result)