import os
import sal_parser
# import sal_semantic
import sal_semantic_base
import sal_semantic_checker
import sal_msil


def execute(prog: str, msil_only: bool = False) -> None:
    prog = sal_parser.parse(prog)

    if not msil_only:
        print('ast:')
        print(*prog.tree, sep=os.linesep)
        print()

        print('semantic_check:')
    try:
        checker = sal_semantic_checker.SemanticChecker()
        scope = sal_semantic_checker.prepare_global_scope()
        checker.semantic_check(prog, scope)
        if not msil_only:
            print(*prog.tree, sep=os.linesep)
    except sal_semantic_base.SemanticException as e:
        print('Ошибка: {}'.format(e.message))
        return
    if not msil_only:
        print()

    # if not msil_only:
        print('msil:')
    try:
        gen = sal_msil.CodeGenerator()
        gen.msil_gen_program(prog)
        print(*gen.code, sep=os.linesep)
    except sal_msil.MsilException or Exception as e:
        print(f'Ошибка {e.message}')
        exit(3)
    if not msil_only:
        print()
