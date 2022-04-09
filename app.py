import os
import sal_parser


def main():
    prog = sal_parser.parse('''
       алг Func(арг цел n)
            нач
                цел i
                цел n
                ввод n
                лог flag := не 3 > 2 и да или не нет
                нц для i от 2 до n
                    если 2 < 3
                        то n := n + 0
                    все
                кц
                
                вещ v
                лог flag :=  5 < n
                если n < 10
                    то v := 0.5
                    иначе v := 1.5
                        нц
                            Func2()
                            вывод tuy
                        кц_при 5>4
                все
                
                нц пока 1 < n * 10
                    
                кц
                
        
                сим s
                лит str := eq
                вывод str, str2
            кон
        
        
        алг Func2()
            нач
                вывод 31
            кон
    ''')
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
