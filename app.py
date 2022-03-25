import os
import sal_parser


def main():
    prog = sal_parser.parse('''
    
            ввод a ввод b  /* comment 1
            ввод c
            */
            c := a + b * (2 - 1) + 0  // comment 2
            вывод c + 1
    
            если a + b
                то
                нц пока a
                    a := a + b
                кц
                иначе
                    если 1 < 2
                        то a := a + b
    
            нц для i от 2 до 4
                c := c + 1
                вывод c
            кц
            
            нц
                t := func
            кц_при t >= 2
        
    ''')
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
