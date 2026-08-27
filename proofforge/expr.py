"""Compact symbolic expression trees, vectorized over batches of states.

Both the controller u(x) and the Lyapunov proof V(x) are trees over these
features of the state x = (theta, omega):

    0: theta   1: omega   2: sin(theta)   3: cos(theta)-1

cos(theta)-1 (not cos(theta)) is used so the feature is 0 at the origin --
handy for building Lyapunov functions that vanish at the upright position.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

FEATURES = ("theta", "omega", "sin_theta", "cosm1_theta")
N_FEAT = len(FEATURES)

OPS_BIN = ("+", "-", "*")
OPS_UN = ("neg", "square")

_CONSTS = np.array([0.5, 1.0, 2.0, 3.0, 5.0, 10.0, -1.0, -2.0, 0.1], dtype=float)


def features_from_state(X: np.ndarray) -> np.ndarray:
    """(M,2) states -> (M,N_FEAT) feature matrix."""
    X = np.atleast_2d(np.asarray(X, dtype=float))
    theta, omega = X[:, 0], X[:, 1]
    return np.stack([theta, omega, np.sin(theta), np.cos(theta) - 1.0], axis=1)


@dataclass
class Node:
    op: str
    children: tuple = ()
    value: float = 0.0
    feat: int = -1

    def copy(self) -> "Node":
        return Node(self.op, tuple(c.copy() for c in self.children), self.value, self.feat)

    def size(self) -> int:
        return 1 + sum(c.size() for c in self.children)

    def depth(self) -> int:
        return 1 if not self.children else 1 + max(c.depth() for c in self.children)

    def eval(self, F: np.ndarray) -> np.ndarray:
        op = self.op
        if op == "const":
            return np.full(F.shape[0], self.value, dtype=float)
        if op == "feat":
            return F[:, self.feat]
        if op == "neg":
            return -self.children[0].eval(F)
        if op == "square":
            a = self.children[0].eval(F)
            return a * a
        a = self.children[0].eval(F)
        b = self.children[1].eval(F)
        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        raise ValueError(f"unknown op {op}")

    def to_math(self) -> str:
        if self.op == "const":
            return f"{self.value:.4g}"
        if self.op == "feat":
            return FEATURES[self.feat]
        if self.op == "neg":
            return f"(-{self.children[0].to_math()})"
        if self.op == "square":
            return f"({self.children[0].to_math()})^2"
        a, b = self.children[0].to_math(), self.children[1].to_math()
        return f"({a} {self.op} {b})"


# --- constructors -----------------------------------------------------------

def C(v: float) -> Node:
    return Node("const", value=float(v))


def F(i: int) -> Node:
    return Node("feat", feat=int(i))


def rand_leaf(rng) -> Node:
    if rng.random() < 0.7:
        return F(int(rng.integers(0, N_FEAT)))
    return C(float(rng.choice(_CONSTS)))


def rand_tree(rng, max_depth: int) -> Node:
    if max_depth <= 1 or (rng.random() < 0.3):
        return rand_leaf(rng)
    if rng.random() < 0.3:
        op = str(rng.choice(OPS_UN))
        return Node(op, (rand_tree(rng, max_depth - 1),))
    op = str(rng.choice(OPS_BIN))
    return Node(op, (rand_tree(rng, max_depth - 1), rand_tree(rng, max_depth - 1)))


def _all_nodes(root: Node) -> list:
    out = [root]
    for c in root.children:
        out.extend(_all_nodes(c))
    return out


def _replace(parent: Node, old: Node, new: Node) -> bool:
    kids = list(parent.children)
    for i, c in enumerate(kids):
        if c is old:
            kids[i] = new
            parent.children = tuple(kids)
            return True
        if _replace(c, old, new):
            return True
    return False


def mutate(node: Node, rng, max_depth: int) -> Node:
    node = node.copy()
    nodes = _all_nodes(node)
    tgt = nodes[int(rng.integers(0, len(nodes)))]
    r = rng.random()
    if r < 0.4 or tgt is node:
        sub = rand_tree(rng, max(1, max_depth - 1))
        if tgt is node:
            return sub
        _replace(node, tgt, sub)
        return node
    if tgt.op == "const":
        tgt.value += float(rng.normal(0, 0.7))
    elif tgt.op == "feat":
        tgt.feat = int(rng.integers(0, N_FEAT))
    elif tgt.op in OPS_UN:
        tgt.op = str(rng.choice(OPS_UN))
    elif tgt.op in OPS_BIN:
        tgt.op = str(rng.choice(OPS_BIN))
    return node


def crossover(a: Node, b: Node, rng) -> tuple:
    a, b = a.copy(), b.copy()
    na, nb = _all_nodes(a), _all_nodes(b)
    sa = na[int(rng.integers(0, len(na)))]
    sb = nb[int(rng.integers(0, len(nb)))]
    if sa is a:
        return sb.copy(), b
    if sb is b:
        _replace(a, sa, sb.copy())
        return a, sa.copy()
    _replace(a, sa, sb.copy())
    return a, b


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    X = np.array([[0.0, 0.0], [0.3, -0.2], [1.0, 2.0]])
    Fm = features_from_state(X)
    # A hand Lyapunov: V = theta^2 + 0.1*omega^2  (>=0, zero at origin)
    V = Node("+", (Node("square", (F(0),)), Node("*", (C(0.1), Node("square", (F(1),))))))
    print("V(x) =", V.to_math(), "=>", V.eval(Fm))
    print("random tree:", rand_tree(rng, 3).to_math())
