import os
import sal_parser


def main():
    prog = sal_parser.parse('''
       алг Func()
        нач
            цел t := 23
            t := 32
            ввод a ввод b  /* comment 1
            ввод c
            */
            c := a + b * (2 - 1) + 0  // comment 2
            вывод c + 1
    
            если a < b
                то
                нц пока a < 2
                    a := a + b
                кц
                иначе
                    если 1 < 2
                        то a := a + b
                    все
            все
    
            нц для i от 2 до 4
                c := c + 1
                w := Func3(38)
                вывод c
            кц
            
            нц
                t := Func2()
            кц_при t >= 2
        кон
        
    алг Func2()
        нач
            вывод 2+num
        кон
        
    алг Func3(арг цел t)
        нач
        кон
    ''')
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
