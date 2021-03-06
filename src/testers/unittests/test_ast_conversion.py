#!/usr/bin/env python3
# coding: utf-8
"""Test AST conversion."""

import operator
import random
import unittest
import utils

from triton import *



class TestAstConversion(unittest.TestCase):

    """Testing the AST conversion Triton <-> z3."""

    def setUp(self):
        self.ctx = TritonContext()
        self.ctx.setArchitecture(ARCH.X86_64)

        self.astCtxt = self.ctx.getAstContext()

        self.sv1 = self.ctx.newSymbolicVariable(8)
        self.sv2 = self.ctx.newSymbolicVariable(8)

        self.v1 = self.astCtxt.variable(self.sv1)
        self.v2 = self.astCtxt.variable(self.sv2)

    def do_test_binop(self):
        """
        Check python binary operation.

        Fuzz int8/uint8 binop values and check triton/z3 and python results.
        """
        # No simplification available
        # This only going to test Triton <-> z3 AST conversions.
        binop = [
            # Overloaded operators
            operator.and_,
            operator.add,
            operator.sub,
            operator.xor,
            operator.or_,
            operator.mul,
            operator.lshift,
            operator.rshift,
            operator.eq,
            operator.ne,
            operator.le,
            operator.ge,
            operator.lt,
            operator.gt,
            operator.floordiv,
            operator.mod,
        ]
        operator_div = operator.floordiv
        if hasattr(operator, "div"):
            operator_div = operator.div
            binop.append(operator_div)

        for _ in range(100):
            cv1 = random.randint(0, 255)
            cv2 = random.randint(0, 255)
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            self.ctx.setConcreteVariableValue(self.sv2, cv2)
            for op in binop:
                n = op(self.v1, self.v2)
                if op in (operator.floordiv, operator_div) and cv2 == 0:
                    ref = 255
                elif op == operator.mod and cv2 == 0:
                    ref = cv1
                else:
                    ref = op(cv1, cv2) % (2 ** 8)
                self.assertEqual(
                    ref,
                    n.evaluate(),
                    "ref = {} and triton value = {} with operator {} operands were {} and {}".format(ref, n.evaluate(), op, cv1, cv2)
                )
                self.assertEqual(ref, self.ctx.evaluateAstViaSolver(n))
                self.assertEqual(ref, self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_binop_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_binop()

    def test_binop_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_binop()

    def do_test_unop(self):
        """
        Check python unary operation.

        Fuzz int8/uint8 binop values and check triton/z3 and python results.
        """
        # No simplification available
        # This only going to test Triton <-> z3 AST conversions.
        unop = [
            operator.invert,
            operator.neg,
        ]

        for cv1 in range(0, 256):
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            for op in unop:
                n = op(self.v1)
                ref = op(cv1) % (2 ** 8)
                self.assertEqual(ref, n.evaluate(),
                                 "ref = {} and triton value = {} with operator "
                                 "{} operands was {}".format(ref,
                                                             n.evaluate(),
                                                             op,
                                                             cv1))
                self.assertEqual(ref, self.ctx.evaluateAstViaSolver(n))
                self.assertEqual(ref, self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_unop_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_unop()

    def test_unop_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_unop()

    def do_test_smtbinop(self):
        """
        Check smt binary operation.

        Fuzz int8/uint8 binop values and check triton/z3 and python results.
        """
        # No simplification available
        # This only going to test Triton <-> z3 AST conversions.
        smtbinop = [
            # AST API
            self.astCtxt.bvadd,
            self.astCtxt.bvand,
            self.astCtxt.bvlshr,
            self.astCtxt.bvashr,
            self.astCtxt.bvmul,
            self.astCtxt.bvnand,
            self.astCtxt.bvnor,
            self.astCtxt.bvor,
            self.astCtxt.bvsdiv,
            self.astCtxt.bvsge,
            self.astCtxt.bvsgt,
            self.astCtxt.bvshl,
            self.astCtxt.bvsle,
            self.astCtxt.bvslt,
            self.astCtxt.bvsmod,
            self.astCtxt.bvsrem,
            self.astCtxt.bvsub,
            self.astCtxt.bvudiv,
            self.astCtxt.bvuge,
            self.astCtxt.bvugt,
            self.astCtxt.bvule,
            self.astCtxt.bvult,
            self.astCtxt.bvurem,
            self.astCtxt.bvxnor,
            self.astCtxt.bvxor,
            self.astCtxt.concat,
            self.astCtxt.distinct,
            self.astCtxt.equal,
            self.astCtxt.iff,
            self.astCtxt.land,
            self.astCtxt.lor,
            self.astCtxt.lxor,
        ]

        for _ in range(100):
            cv1 = random.randint(0, 255)
            cv2 = random.randint(0, 255)
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            self.ctx.setConcreteVariableValue(self.sv2, cv2)
            for op in smtbinop:
                if op == self.astCtxt.concat:
                    n = op([self.v1, self.v2])
                elif op in (self.astCtxt.land, self.astCtxt.lor, self.astCtxt.lxor):
                    n = op([self.v1 != cv1, self.v2 != cv2])
                elif op == self.astCtxt.iff:
                    n = op(self.v1 > cv1, self.v2 < cv2)
                else:
                    n = op(self.v1, self.v2)
                self.assertEqual(
                    n.evaluate(),
                    self.ctx.evaluateAstViaSolver(n),
                    "triton = {} and z3 = {} with operator {} operands were {} and {}".format(n.evaluate(), self.ctx.evaluateAstViaSolver(n), op, cv1, cv2)
                )
                self.assertEqual(
                    n.evaluate(),
                    self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate(),
                    "triton = {} and z3 = {} with operator {} operands were {} and {}".format(n.evaluate(), self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate(), op, cv1, cv2)
                )

    def test_smtbinop_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_smtbinop()

    def test_smtbinop_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_smtbinop()

    def do_test_smt_unop(self):
        """
        Check python unary operation.

        Fuzz int8/uint8 binop values and check triton/z3 and python results.
        """
        # No simplification available
        # This only going to test Triton <-> z3 AST conversions.
        smtunop = [
            self.astCtxt.bvneg,
            self.astCtxt.bvnot,
            self.astCtxt.lnot,
            lambda x: self.astCtxt.bvrol(x, self.astCtxt.bv(2, x.getBitvectorSize())),
            lambda x: self.astCtxt.bvror(x, self.astCtxt.bv(3, x.getBitvectorSize())),
            lambda x: self.astCtxt.sx(16, x),
            lambda x: self.astCtxt.zx(16, x),
        ]

        for cv1 in range(0, 256):
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            for op in smtunop:
                if op == self.astCtxt.lnot:
                    n = op(self.v1 != 0)
                else:
                    n = op(self.v1)
                self.assertEqual(n.evaluate(), self.ctx.evaluateAstViaSolver(n))
                self.assertEqual(n.evaluate(), self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_smt_unop_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_smt_unop()

    def test_smt_unop_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_smt_unop()

    def do_test_bvnode(self):
        """Check python bit vector declaration."""
        for _ in range(100):
            cv1 = random.randint(-127, 255)
            n = self.astCtxt.bv(cv1, 8)
            self.assertEqual(n.evaluate(), self.ctx.evaluateAstViaSolver(n))
            self.assertEqual(n.evaluate(), self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_bvnode_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_bvnode()

    def test_bvnode_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_bvnode()

    def do_test_extract(self):
        """Check bit extraction from bitvector."""
        for _ in range(100):
            cv1 = random.randint(0, 255)
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            for lo in range(0, 8):
                for hi in range(lo, 8):
                    n = self.astCtxt.extract(hi, lo, self.v1)
                    ref = ((cv1 << (7 - hi)) % 256) >> (7 - hi + lo)
                    self.assertEqual(ref, n.evaluate(),
                                     "ref = {} and triton value = {} with operator"
                                     "'extract' operands was {} low was : {} and "
                                     "hi was : {}".format(ref, n.evaluate(), cv1, lo, hi))
                    self.assertEqual(ref, self.ctx.evaluateAstViaSolver(n))
                    self.assertEqual(ref, self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_extract_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_extract()

    def test_extract_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_extract()

    def do_test_ite(self):
        """Check ite node."""
        for _ in range(100):
            cv1 = random.randint(0, 255)
            cv2 = random.randint(0, 255)
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            self.ctx.setConcreteVariableValue(self.sv2, cv2)
            n = self.astCtxt.ite(self.v1 < self.v2, self.v1, self.v2)
            self.assertEqual(n.evaluate(), self.ctx.evaluateAstViaSolver(n))
            self.assertEqual(n.evaluate(), self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_ite_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_ite()

    def test_ite_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_ite()

    @utils.xfail
    def do_test_integer(self):
        # Decimal node is not exported in the python interface
        for cv1 in range(0, 256):
            n = self.astCtxt.integer(cv1)
            self.assertEqual(n.evaluate(), self.ctx.evaluateAstViaSolver(n))
            self.assertEqual(n.evaluate(), self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_integer_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_integer()

    def test_integer_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_integer()

    @utils.xfail
    def do_test_let(self):
        # Let node didn't take the variable in its computation
        for run in range(100):
            cv1 = random.randint(0, 255)
            cv2 = random.randint(0, 255)
            self.ctx.setConcreteVariableValue(self.sv1, cv1)
            self.ctx.setConcreteVariableValue(self.sv2, cv2)
            n = self.astCtxt.let("b", self.astCtxt.bvadd(self.v1, self.v2), self.astCtxt.bvadd(self.astCtxt.string("b"), self.v1))
            self.assertEqual(n.evaluate(), self.ctx.evaluateAstViaSolver(n))
            self.assertEqual(n.evaluate(), self.ctx.simplify(n, solver=True if self.ctx.getSolver() == SOLVER.Z3 else False).evaluate())

    def test_let_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_let()

    def test_let_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_let()

    def do_test_fuzz(self):
        """
        Fuzz test an ast evaluation.

        It creates an ast node of depth 10 and evaluate it with triton and z3
        and compare result.
        """
        self.in_bool = [
            (self.astCtxt.lnot, 1),
            (self.astCtxt.land, 2),
            (self.astCtxt.lor, 2),
            (self.astCtxt.lxor, 2),
            (self.astCtxt.iff, 2),
        ]
        self.to_bool = [
            (self.astCtxt.bvsge, 2),
            (self.astCtxt.bvsgt, 2),
            (self.astCtxt.bvsle, 2),
            (self.astCtxt.bvslt, 2),
            (self.astCtxt.bvuge, 2),
            (self.astCtxt.bvugt, 2),
            (self.astCtxt.bvule, 2),
            (self.astCtxt.bvult, 2),
            (self.astCtxt.equal, 2),
        ] + self.in_bool
        self.bvop = [
            (self.astCtxt.bvneg, 1),
            (self.astCtxt.bvnot, 1),
            (lambda x: self.astCtxt.bvrol(x, self.astCtxt.bv(3, x.getBitvectorSize())), 1),
            (lambda x: self.astCtxt.bvror(x, self.astCtxt.bv(2, x.getBitvectorSize())), 1),
            (lambda x: self.astCtxt.extract(11, 4, self.astCtxt.sx(16, x)), 1),
            (lambda x: self.astCtxt.extract(11, 4, self.astCtxt.zx(16, x)), 1),

            # BinOp
            (self.astCtxt.bvadd, 2),
            (self.astCtxt.bvand, 2),
            (self.astCtxt.bvlshr, 2),
            (self.astCtxt.bvashr, 2),
            (self.astCtxt.bvmul, 2),
            (self.astCtxt.bvnand, 2),
            (self.astCtxt.bvnor, 2),
            (self.astCtxt.bvor, 2),
            (self.astCtxt.bvsdiv, 2),
            (self.astCtxt.bvshl, 2),
            (self.astCtxt.bvsmod, 2),
            (self.astCtxt.bvsrem, 2),
            (self.astCtxt.bvsub, 2),
            (self.astCtxt.bvudiv, 2),
            (self.astCtxt.bvurem, 2),
            (self.astCtxt.bvxnor, 2),
            (self.astCtxt.bvxor, 2),
            (lambda x, y: self.astCtxt.concat([self.astCtxt.extract(3, 0, x), self.astCtxt.extract(7, 4, y)]), 2),

            (self.astCtxt.ite, -1),

            # value
            (self.v1, 0),
            (self.v2, 0),
        ]
        for _ in range(10):
            n = self.new_node(0, self.bvop)
            for _ in range(10):
                cv1 = random.randint(0, 255)
                cv2 = random.randint(0, 255)
                self.ctx.setConcreteVariableValue(self.sv1, cv1)
                self.ctx.setConcreteVariableValue(self.sv2, cv2)
                self.assertEqual(n.evaluate(), self.ctx.evaluateAstViaSolver(n))

    def test_fuzz_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_fuzz()

    def test_fuzz_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_fuzz()

    def new_node(self, depth, possible):
        """Recursive function to create a random ast."""
        if depth >= 10:
            # shortcut if the tree is deep enough
            possible = possible[-2:]

        op, nargs = random.choice(possible)
        if op == self.astCtxt.ite:
            return op(self.new_node(depth, self.to_bool),
                      self.new_node(depth + 1, self.bvop),
                      self.new_node(depth + 1, self.bvop))
        elif any(op == ibo for ibo, _ in self.in_bool):
            args = [self.new_node(depth, self.to_bool) for _ in range(nargs)]
            if op in (self.astCtxt.land, self.astCtxt.lor, self.astCtxt.lxor):
                return op(args)
            else:
                return op(*args)
        elif nargs == 0:
            return op
        else:
            return op(*[self.new_node(depth + 1, self.bvop) for _ in range(nargs)])


class TestUnrollAst(unittest.TestCase):

    """Testing unroll AST."""

    def setUp(self):
        """Define the arch."""
        self.ctx = TritonContext()
        self.ctx.setArchitecture(ARCH.X86_64)
        self.ast = self.ctx.getAstContext()

    def do_test_1(self):
        self.ctx.processing(Instruction(b"\x48\xc7\xc0\x01\x00\x00\x00")) # mov rax, 1
        self.ctx.processing(Instruction(b"\x48\x89\xc3")) # mov rbx, rax
        self.ctx.processing(Instruction(b"\x48\x89\xd9")) # mov rcx, rbx
        self.ctx.processing(Instruction(b"\x48\x89\xca")) # mov rdx, rcx
        rdx = self.ctx.getRegisterAst(self.ctx.registers.rdx)
        self.assertEqual(str(rdx), "ref!6")
        self.assertEqual(str(self.ast.unroll(rdx)), "(_ bv1 64)")
        return

    def test_1_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_1()

    def test_1_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_1()

    def do_test_2(self):
        self.ctx.processing(Instruction(b"\x48\xc7\xc0\x01\x00\x00\x00")) # mov rax, 1
        self.ctx.processing(Instruction(b"\x48\x31\xc0")) # xor rax, rax
        rax = self.ctx.getRegisterAst(self.ctx.registers.rax)
        self.assertEqual(str(rax), "ref!2")
        self.assertEqual(str(self.ast.unroll(rax)), "(bvxor (_ bv1 64) (_ bv1 64))")
        return

    def test_2_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_2()

    def test_2_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_2()

    def do_test_3(self):
        self.ctx.processing(Instruction(b"\x48\xc7\xc0\x01\x00\x00\x00")) # mov rax, 1
        self.ctx.processing(Instruction(b"\x48\xc7\xc3\x02\x00\x00\x00")) # mov rbx, 2
        self.ctx.processing(Instruction(b"\x48\x31\xd8")) # xor rax, rbx
        self.ctx.processing(Instruction(b"\x48\xff\xc0")) # inc rax
        self.ctx.processing(Instruction(b"\x48\x89\xc2")) # mov rdx, rax
        rdx = self.ctx.getRegisterAst(self.ctx.registers.rdx)
        self.assertEqual(str(rdx), "ref!18")
        self.assertEqual(str(self.ast.unroll(rdx)), "(bvadd (bvxor (_ bv1 64) (_ bv2 64)) (_ bv1 64))")
        ref4 = self.ctx.getSymbolicExpression(4)
        self.assertEqual(str(ref4.getAst()), "(bvxor ref!0 ref!2)")
        return

    def test_3_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test_3()

    def test_3_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test_3()


class TestAstTraversal(unittest.TestCase):

    """Testing AST traversal."""
    def setUp(self):
        """Define the arch."""
        self.ctx = TritonContext()
        self.ctx.setArchitecture(ARCH.X86_64)
        self.ast = self.ctx.getAstContext()

    def do_test(self):
        a = self.ast.bv(1, 8)
        b = self.ast.bv(2, 8)
        c = a ^ b
        d = c + a
        e = d + b
        f = e + e
        g = f + b
        ref1 = self.ast.reference(self.ctx.newSymbolicExpression(g))
        ref2 = self.ast.reference(self.ctx.newSymbolicExpression(a))
        k = ref1 + ref2
        self.assertEqual(k.evaluate(), self.ctx.evaluateAstViaSolver(k))

    def test_z3(self):
        if 'Z3' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.Z3)
            self.do_test()

    def test_bitwuzla(self):
        if 'BITWUZLA' in dir(SOLVER):
            self.ctx.setSolver(SOLVER.BITWUZLA)
            self.do_test()
