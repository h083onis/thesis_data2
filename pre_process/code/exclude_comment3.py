from enum import Enum

class State(Enum):
    CODE = 1
    C_COMMENT = 2
    CPP_COMMENT = 3
    PYTHON_LINE_COMMENT = 5
    PYTHON_MULTI_COMMENT_SINGLE = 7
    PYTHON_MULTI_COMMENT_DUBBLE = 8
    STRING_SINGLE_LITERAL = 9
    STRING_DUBLE_LITERAL = 10
    STRING_SINGLE_LITERAL_OR_COMMENT = 11
    STRING_DUBLE_LITERAL_OR_COMMENT = 12

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
        result = []  # filtered text (char array)
        prev = ''  # previous char
        pprev = ''  # previous previous char
        state = State.CODE
        escape_cnt = 0
        is_line_start = True
        tmp = []
        
        for ch in text:
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
                    result.append('\n')
                    pprev = prev = ''
                else:
                    pprev, prev = prev, ch
                continue
            
            if state == State.PYTHON_MULTI_COMMENT_SINGLE:
                if escape_cnt % 2 == 0 and pprev == '\'' and prev == '\'' and ch == '\'':
                    state = State.CODE
                    pprev = prev = ''
                    escape_cnt = 0
                    continue
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                if ch == '\n':
                    result.append('\n')
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
                # print(prev)
                continue
            
            if state == State.STRING_DUBLE_LITERAL:
                if escape_cnt % 2 == 0 and ch == '"':
                    state = State.CODE
                    escape_cnt = 0
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                result.append(prev)
                pprev, prev = prev, ch
                continue
            
            # Starts comment?
            if escape_cnt % 2 == 0 and ch == '#':
                state = State.PYTHON_LINE_COMMENT
                pprev = prev = ''
                escape_cnt = 0
                continue
            
            # STRING_DUBLE_LITERAL OR COMMENT?
            if state == State.STRING_DUBLE_LITERAL_OR_COMMENT:
                tmp.append(prev)
                if is_line_start == True and escape_cnt % 2 == 0 and pprev == '"' and prev == '"' and ch == '"':
                    state = State.PYTHON_MULTI_COMMENT_DUBBLE
                    pprev = prev = ''
                    escape_cnt = 0
                    tmp = []
                elif escape_cnt % 2 == 0 and ch != '"':
                    state = State.STRING_DUBLE_LITERAL
                    result.extend(tmp)
                    escape_cnt = 0
                    tmp = []
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                pprev, prev = prev, ch
                continue
            
            # STRING_SINGLE_LITERAL OR COMMENT?
            if state == State.STRING_SINGLE_LITERAL_OR_COMMENT:
                tmp.append(prev)
                if escape_cnt % 2 == 0 and pprev == '\'' and prev == '\'' and ch == '\'':
                    state = State.PYTHON_MULTI_COMMENT_SINGLE
                    pprev = prev = ''
                    escape_cnt = 0
                    tmp = []
                elif pprev == '\'' and prev == '\'' and ch != '\'':
                    state = State.CODE
                    result.extend(tmp)
                    escape_cnt = 0
                    tmp = []
                elif escape_cnt % 2 == 0 and ch != '\'':
                    state = State.STRING_SINGLE_LITERAL
                    result.extend(tmp)
                    escape_cnt = 0
                    tmp = []
                if ch == '\\':
                    escape_cnt += 1
                else:
                    escape_cnt = 0
                # print(pprev,prev,ch)
                pprev, prev = prev, ch
                continue
            
            if ch == '\\':
                escape_cnt += 1
            else:
                escape_cnt = 0
            
            #is ch for the first time in line
            if ch != ' ' and ch != '"' and ch != '\'':
                is_line_start = False
            if ch == '\n':
                is_line_start = True
                  
            # Starts string_literal or Comment (DUBLE)?
            if escape_cnt % 2 == 0 and ch == '"':
                if is_line_start == False:
                    state = State.STRING_DUBLE_LITERAL
                else: 
                    state = State.STRING_DUBLE_LITERAL_OR_COMMENT
                escape_cnt = 0
                
            # Starts string literal or Comment (SINGLE)?
            if escape_cnt % 2 == 0 and ch == "'":
                if is_line_start == False:
                    state = State.STRING_SINGLE_LITERAL
                else:
                    state = State.STRING_SINGLE_LITERAL_OR_COMMENT
                escape_cnt = 0
            # print(ch)
            # Comment has not started yet
            if prev: result.append(prev)
            pprev, prev = prev, ch

        # Returns filtered text
        if prev: result.append(prev)
        return ''.join(result)