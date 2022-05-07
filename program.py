import os
import sal_parser
# import sal_semantic


def execute(prog: str) -> None:
    prog = sal_parser.parse(prog)

    print('ast:')
    print(*prog.tree, sep=os.linesep)
    print()

    # print('semantic_check:')
    # try:
    #     scope = sal_semantic.prepare_global_scope()
    #     prog.semantic_check(scope)
    #     print(*prog.tree, sep=os.linesep)
    # except sal_semantic.SemanticException as e:
    #     print('Ошибка: {}'.format(e.message))
    #     return
    # print()