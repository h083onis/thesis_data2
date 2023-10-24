from enum import Enum
import ast
import astor

class State(Enum):
    CODE = 1
    C_COMMENT = 2
    CPP_COMMENT = 3
    PYTHON_LINE_COMMENT = 5
    PYTHON_MULTI_COMMENT_DUBBLE = 6
    PYTHON_MULTI_COMMENT_SINGLE = 7
    STRING_SINGLE_LITERAL = 8
    STRING_DUBLE_LITERAL = 9
    STRING_LITERAL_OR_COMMENT = 10

def exclude_comment(text, ext):
    if ext == 'java' or ext == 'cpp' or ext== 'hpp' or ext == 'c' or ext == 'h':
        result = []
        prev = ''
        pprev = ''
        ppprev = ''
        state = State.CODE
        escape_cnt = 0

        for ch in text:
            # Skip to the end of C-style comment
            if state == State.C_COMMENT:
                if (pprev != '\\' and prev == '*' and ch == '/') or (ppprev == '\\' and pprev =='\\' and prev =='*' and ch == '/'):  # End comment
                    state = State.CODE
                    ppprev = pprev = prev = ''
                elif ch == '\n':
                    # result.append('\n')
                    ppprev = pprev = prev = ''
                else:
                    ppprev, pprev, prev = pprev, prev, ch
                continue

            # Skip to the end of the line (C++ style comment)
            if state == State.CPP_COMMENT:
                if ch == '\n':  # End comment
                    state = State.CODE
                    result.append('\n')
                    ppprev = pprev = prev = ''
                continue

            # Skip to the end of the string literal
            #\\エスケープ文字の数を数えて奇数，偶数で対応を返る必要性がある
            if state == State.STRING_DUBLE_LITERAL:
                # if ch == '\\':
                #     escape_cnt += 1
                # if escape_cnt % 2 == 0 and ch == '"':
                #     state = State.CODE
                #     escape_cnt = 0
                if (prev != '\\' and ch == '"') or (ppprev != '\\' and pprev =='\\' and prev == '\\' and ch == '"'):  # End literal
                    state = State.CODE
                print(prev)
                result.append(prev)
                ppprev, pprev, prev = pprev, prev, ch
                continue
            
             # Skip to the end of the string literal
            if state == State.STRING_SINGLE_LITERAL:
                if (prev != '\\' and ch == '\'') or (ppprev != '\\' and pprev =='\\' and prev == '\\' and ch == '\''):  # End literal
                    state = State.CODE
                # print(prev)
                result.append(prev)
                ppprev, pprev, prev = pprev, prev, ch
                continue

            # Starts C-style comment?
            if (pprev != '\\' and prev == '/' and ch == '*') or (ppprev == '\\' and pprev == '\\' and prev == '/' and ch == '*'):
                state = State.C_COMMENT
                ppprev = pprev = prev = ''
                continue

            # Starts C++ style comment?
            if (pprev != '\\' and prev == '/' and ch == '/') or (ppprev == '\\' and pprev == '\\' and prev == '/' and ch == '/'):
                state = State.CPP_COMMENT
                ppprev = pprev = prev = ''
                continue

            # Comment has not started yet
            if prev: result.append(prev)

            # Starts string literal?
            if (prev !='\\' and ch == '\'') or (ppprev != '\\' and pprev == '\\' and prev == '\\' and ch == '\''):
                state = State.STRING_SINGLE_LITERAL
            ppprev, pprev, prev = pprev, prev, ch
            
            # Starts string literal?
            if (prev !='\\' and ch == '"') or (ppprev != '\\' and pprev == '\\' and prev == '\\' and ch == '"'):
                state = State.STRING_DUBLE_LITERAL
            ppprev, pprev, prev = pprev, prev, ch

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
        ppprev = '' # previous previous previous char
        pppprev = ''
        state = State.CODE

        for ch in rebuilt_source_code:
            # Skip to the end of C-style comment
            if state == State.PYTHON_MULTI_COMMENT_DUBBLE:
                if (ppprev != '\\' and pprev == '"' and prev == '"' and ch == '"') or (pppprev == '\\' and ppprev == '\\' and pprev == '"' and prev == '"' and ch == '"'):  # End comment
                    state = State.CODE
                    pppprev = ppprev = pprev = prev = ''
                elif ch == '\n':
                    result.append('\n')
                    pppprev = ppprev = pprev = prev = ''
                else:
                    pppprev, ppprev, pprev, prev = ppprev, pprev, prev, ch
                continue

            # Skip to the end of the line (C++ style comment)
            if state == State.PYTHON_LINE_COMMENT:
                if ch == '\n':  # End comment
                    state = State.CODE
                    result.append('\n')
                    pppprev = ppprev = pprev = prev = ''
                continue

            # Skip to the end of the string literal
            if state == State.STRING_SINGLE_LITERAL:
                if (prev != '\\' and ch == "'") or (ppprev != '\\' and pprev == '\\' and prev == '\\' and ch == "'"):
                    state = State.CODE
                result.append(prev)
                pppprev, ppprev, pprev, prev = ppprev, pprev, prev, ch
                continue
            
            if state == State.STRING_DUBLE_LITERAL:
                if (prev != '\\' and ch == '"') or (ppprev != '\\' and pprev =='\\' and prev == '\\' and ch == '"'):  # End literal
                    state = State.CODE
                # print(prev)
                result.append(prev)
                pppprev, ppprev, pprev, prev = ppprev, pprev, prev, ch
                continue
            
            # Starts comment?
            if (prev != '\\' and ch == '#') or (ppprev != '\\' and pprev == '\\' and prev == '\\' and ch == '#'):
                state = State.PYTHON_LINE_COMMENT
                pppprev = ppprev = pprev = prev = ''
                continue
            
            # STRING_LITERAL OR COMMENT?
            if state == State.STRING_LITERAL_OR_COMMENT:
                if (ppprev != '\\' and pprev == '"' and prev == '"' and ch == '"') or (pppprev == '\\' and ppprev == '\\' and pprev == '"' and prev == '"' and ch == '"'):
                    state = State.PYTHON_MULTI_COMMENT_DUBBLE
                    ppprev = pprev = prev = ''
                    
                elif prev !='\\' and ch != '"':
                    state = State.STRING_DUBLE_LITERAL
                    result.extend([pprev,prev])

                pppprev, ppprev, pprev, prev = ppprev, pprev, prev, ch
                continue
            
            # Starts string literal or Comment?
            if (prev !='\\' and ch == '"') or (ppprev != '\\' and pprev == '\\' and prev == '\\' and ch == '"'):
                state = State.STRING_LITERAL_OR_COMMENT
                pppprev, ppprev, pprev, prev = ppprev, pprev, prev, ch
                continue
                
            # Starts string literal?
            if (prev !='\\' and ch == '\'') or (ppprev != '\\' and pprev == '\\' and prev == '\\' and ch == '\''):
                state = State.STRING_SINGLE_LITERAL

            # Comment has not started yet
            if prev: result.append(prev)
            pppprev, ppprev, pprev, prev = ppprev, pprev, prev, ch

        # Returns filtered text
        if prev: result.append(prev)
        return ''.join(result)
    
    # elif ext == 'py':
    #     parsed_code = ast.parse(text)
    #     rebuilt_source_code = "\n".join(astor.to_source(parsed_code).splitlines())
        
    #     result = []  # filtered text (char array)
    #     prev = ''  # previous char
    #     pprev = ''  # previous previous char
    #     ppprev = '' # previous previous previous char
    #     state = State.CODE
    #     state2 = State.CODE

    #     for ch in rebuilt_source_code:
    #         # Skip to the end of C-style comment
    #         if state == State.PYTHON_MULTI_COMMENT_DUBBLE:
    #             if ppprev != '\\' and pprev == '"' and prev == '"' and ch == '"':  # End comment
    #                 state = State.CODE
    #                 ppprev = pprev = prev = ''
    #             elif ch == '\n':
    #                 result.append('\n')
    #                 ppprev = pprev = prev = ''
    #             else:
    #                 ppprev, pprev, prev = pprev, prev, ch
    #             continue
            
    #         if state == State.PYTHON_MULTI_COMMENT_SINGLE:
    #             if ppprev != '\\' and pprev == "'" and prev == "'" and ch == "'":  # End comment
    #                 state = State.CODE
    #                 ppprev = pprev = prev = ''
    #             elif ch == '\n':
    #                 result.append('\n')
    #                 ppprev = pprev = prev = ''
    #             else:
    #                 ppprev, pprev, prev = pprev, prev, ch
    #             continue

    #         # Skip to the end of the line (C++ style comment)
    #         if state == State.PYTHON_LINE_COMMENT:
    #             if ch == '\n':  # End comment
    #                 state = State.CODE
    #                 result.append('\n')
    #                 ppprev = pprev = prev = ''
    #             continue

    #         # Skip to the end of the string literal
    #         if state == State.STRING_LITERAL:
    #             if prev != '\\' and ch == '"' and state2 == State.STRING_DUBLE_LITERAL:  # End literal
    #                 state = state2 = State.CODE
                    
    #             elif prev != '\\' and ch == "'" and state2 == State.STRING_SINGLE_LITERAL:
    #                 state = state2 = State.CODE
    #             # print(ch+'2')
    #             result.append(prev)
    #             ppprev, pprev, prev = pprev, prev, ch
    #             continue

    #         # Starts comment?
    #         if prev != '\\' and ch == '#':
    #             state = State.PYTHON_LINE_COMMENT
    #             ppprev = pprev = prev = ''
    #             continue
            
    #         if state == State.STRING_LITERAL_OR_COMMENT and state2 == State.STRING_DUBLE_LITERAL:
    #             if ppprev != '\\' and pprev == '"' and prev == '"' and ch == '"':
    #                 state = State.PYTHON_MULTI_COMMENT_DUBBLE
    #                 ppprev = pprev = prev = ''
    
    #             elif prev !='\\' and ch !='"':
    #                 state = State.STRING_LITERAL
    #                 result.extend([prev])
                
    #             ppprev, pprev, prev = pprev, prev, ch
    #             continue
                
    #         if state == State.STRING_LITERAL_OR_COMMENT and state2 == State.STRING_SINGLE_LITERAL:
    #             if ppprev != '\\' and pprev == "'" and prev == "'" and ch == "'":
    #                 state = State.PYTHON_MULTI_COMMENT_SINGLE
    #                 ppprev = pprev = prev = ''
                    
    #             elif prev !='\\' and ch !="'":
    #                 state = State.STRING_LITERAL
    #                 result.extend([prev])
               
    #             ppprev, pprev, prev = pprev, prev, ch
    #             continue
                    
                                
    #         # Starts string literal or Comment?
    #         if ch == '"' or ch == "'":
    #             state = State.STRING_LITERAL_OR_COMMENT
    #             if ch == '"':
    #                 state2 = State.STRING_DUBLE_LITERAL
    #             else:
    #                 state2 = State.STRING_SINGLE_LITERAL
    #             result.append(prev)
    #             ppprev, pprev, prev = pprev, prev, ch
    #             continue

    #         # Comment has not started yet
    #         if prev: result.append(prev)
    #         ppprev, pprev, prev = pprev, prev, ch

    #     # Returns filtered text
    #     if prev: result.append(prev)
    #     return ''.join(result)
        