import program


def main():
    prog = '''
       алг Func(арг цел n, рез цел res)
            нач
                цел i
                цел n
                ввод n
                лог flag := не (3 > 2 и да) или не нет
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
                        кц_при 5>4.
                все
                
                нц пока 1 < n * 10
                    res := res + 2 
                кц
                
        
                s := 'q'
                лит str := "qq"
                вывод str, "str" + 'w'
            кон
        
        
        алг Func2()
            нач
                вывод 31
            кон
            
        алг Func3(арг лог bool, вещ t, рез сим e)
            нач
                нц для q от 1 до 2
                    если да и q = 1
                        то
                            цел i := 0
                            нц пока нет или не (2 < i)
                                i = i + 1
                            кц
                            цел j := 11
                            нц
                                i = i * 10
                                j := j - 1
                            кц_при  j > 0
                        иначе
                            цел i := 10
                            нц пока нет или не (2 < i)
                                i = i + 10
                            кц
                            цел j := 110
                            нц
                                i = i * Func(j)
                                j := j - 1
                            кц_при  j > 0
                    все
                кц
            кон
    '''

    prog2 = 'цел i := 2'
    #print(*prog.tree, sep=os.linesep)
    program.execute(prog2)


if __name__ == "__main__":
    main()
