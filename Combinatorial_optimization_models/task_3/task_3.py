import time
import typing as tp
from abc import ABC, abstractmethod

import numpy as np

import Combinatorial_optimization_models.task_2_2.hw_2_2 as hw_2

CliqueId = int
VertexId = int


class Instance:
    def __init__(
            self,
            weight: np.array,
            vertex_id_to_clique_id: tp.Optional[tp.List[CliqueId]] = None,
            clique_id_to_vertexes: tp.Optional[tp.Dict[CliqueId, tp.Set[VertexId]]] = None,
            base_solution_type=0
    ):
        self._weight = weight
        self._n = weight.shape[0]
        self._vertex_id_to_clique_id: tp.Optional[tp.List[CliqueId]] = None
        self._clique_id_to_vertexes: tp.Optional[tp.Dict[CliqueId, tp.Set[VertexId]]] = None

        if vertex_id_to_clique_id is not None:
            self._vertex_id_to_clique_id = vertex_id_to_clique_id.copy()
            if clique_id_to_vertexes is not None:
                self._clique_id_to_vertexes = {i: j.copy() for i, j in clique_id_to_vertexes.items()}
            else:
                self._clique_id_to_vertexes = dict()
                for vertex, clique in enumerate(self._vertex_id_to_clique_id):
                    if clique not in self._clique_id_to_vertexes:
                        self._clique_id_to_vertexes[clique] = {vertex}
                    else:
                        self._clique_id_to_vertexes[clique].add(vertex)
        else:
            if base_solution_type == 0:
                self._vertex_id_to_clique_id = [i for i in range(self._n)]
                self._clique_id_to_vertexes = {i: {i} for i in range(self._n)}
            if base_solution_type == 1:
                self._vertex_id_to_clique_id = [0 for _ in range(self._n)]
                self._clique_id_to_vertexes = {0: set(range(self._n))}

        self.renumerate()

    def _mex(self):
        m = 0
        x = {i for i, j in self._clique_id_to_vertexes.items() if len(j) > 0}
        while m in x:
            m += 1
        return m

    def copy(self):
        return Instance(
            self._weight,
            self._vertex_id_to_clique_id.copy()
        )

    @property
    def vertex_number(self):
        return self._n

    def in_one_clique_q(self, *args):
        if len(args) == 1:
            v1, v2 = args[0]
        elif len(args) == 2:
            v1, v2 = args
        else:
            raise ValueError
        return self._vertex_id_to_clique_id[v1] == self._vertex_id_to_clique_id[v2]

    def vertex_in_clique_q(self, vertex_id, clique_id):
        return self._vertex_id_to_clique_id[vertex_id] == clique_id

    def weight(self, *args):
        if len(args) == 1:
            v1, v2 = args[0]
        elif len(args) == 2:
            v1, v2 = args
        else:
            raise ValueError
        return self._weight[v1, v2]

    def edge_iter(self):
        for v1 in range(self.vertex_number):
            for v2 in range(self.vertex_number):
                if v1 < v2:
                    yield v1, v2

    def clique_id_iter(self):
        for i in self._clique_id_to_vertexes:
            yield i

    def clique_iter(self):
        for i, j in self._clique_id_to_vertexes.items():
            yield i

    def obj_value(self):
        val = 0
        for edge in self.edge_iter():
            if self.in_one_clique_q(edge):
                val += self.weight(edge)
        return val

    def renumerate(self):
        mapping = dict()
        c = 0
        for i in self._vertex_id_to_clique_id:
            if i not in mapping:
                mapping[i] = c
                c += 1

        self._vertex_id_to_clique_id = [mapping[i] for i in self._vertex_id_to_clique_id]
        self._clique_id_to_vertexes = {mapping[i]: j for i, j in self._clique_id_to_vertexes.items() if len(j) > 0}

    def get_clique_id(self, vertex_id):
        return self._vertex_id_to_clique_id[vertex_id]

    def get_vertexes(self, clique_id):
        for i in self._clique_id_to_vertexes[clique_id]:
            yield i

    def move(self, vertex_id, clique_id):
        old_cli_id = self._vertex_id_to_clique_id[vertex_id]
        self._clique_id_to_vertexes[old_cli_id].remove(vertex_id)

        self._clique_id_to_vertexes[clique_id].add(vertex_id)

        self._vertex_id_to_clique_id[vertex_id] = clique_id

    def separate(self, vertex):
        clique_id = self._vertex_id_to_clique_id[vertex]
        if len(self._clique_id_to_vertexes[clique_id]) == 1:
            return

        self._clique_id_to_vertexes[clique_id].remove(vertex)
        clique_id_v = self._mex()
        self._vertex_id_to_clique_id[vertex] = clique_id_v
        self._clique_id_to_vertexes[clique_id_v] = {vertex}

    def swap(self, vertex_1, vertex_2):
        clique_id_1 = self._vertex_id_to_clique_id[vertex_1]
        clique_id_2 = self._vertex_id_to_clique_id[vertex_2]
        if clique_id_2 == clique_id_1:
            return

        self.move(vertex_1, clique_id_2)
        self.move(vertex_2, clique_id_1)

    def delta_move(self, vertex, clique_id):
        clique_id_v = self._vertex_id_to_clique_id[vertex]
        if clique_id_v == clique_id:
            return 0

        delta1 = 0
        for i in self._clique_id_to_vertexes[clique_id_v]:
            delta1 -= self._weight[vertex, i]

        delta2 = 0
        for i in self._clique_id_to_vertexes[clique_id]:
            delta2 += self._weight[vertex, i]

        return delta1 + delta2

    def delta_separate(self, vertex):
        delta = 0
        clique_id = self._vertex_id_to_clique_id[vertex]
        for i in self._clique_id_to_vertexes[clique_id]:
            delta -= self._weight[vertex, i]

        return delta

    def delta_swap(self, vertex_1, vertex_2):
        delta = 0
        if self._vertex_id_to_clique_id[vertex_2] == self._vertex_id_to_clique_id[vertex_1]:
            return delta

        delta1 = self.delta_move(
            vertex_1,
            self._vertex_id_to_clique_id[vertex_2]
        )
        delta2 = self.delta_move(
            vertex_2,
            self._vertex_id_to_clique_id[vertex_1],
        )

        return delta1 + delta2 - 2 * self._weight[vertex_1, vertex_2]


class AbstractSolver(ABC):
    @abstractmethod
    def solve(self, instance: Instance):
        raise NotImplementedError()


class BaseSolver(AbstractSolver):
    def solve(self, instance):
        instance = instance.copy()
        n = instance.vertex_number

        for cur_cli_id in range(n):
            for next_vertex in range(n):
                if not instance.vertex_in_clique_q(next_vertex, cur_cli_id):
                    next_cli_id = instance.get_clique_id(next_vertex)

                    delta = 0
                    for i in instance.get_vertexes(next_cli_id):
                        delta -= instance.weight(i, next_vertex)
                    for i in instance.get_vertexes(cur_cli_id):
                        delta += instance.weight(i, next_vertex)

                    if delta > 0:
                        instance.move(next_vertex, cur_cli_id)

        return instance


class LocalSearch(AbstractSolver):
    def __init__(self, step_number=10, strategy_id=0, step_id=0):
        self._step_number = step_number
        self._strategy_id = strategy_id
        self._step_id = step_id

    @staticmethod
    def _strategy_1(instance):
        for vertex in range(instance.vertex_number):
            for clique in instance.clique_id_iter():
                yield instance.delta_move(vertex, clique), instance.move, vertex, clique

        for vertex in range(instance.vertex_number):
            yield instance.delta_separate(vertex), instance.separate, vertex

    @staticmethod
    def _strategy_2(instance):
        for i in LocalSearch._strategy_1(instance):
            yield i

        for v1, v2 in instance.edge_iter():
            yield instance.delta_swap(v1, v2), instance.swap, v1, v2

    @staticmethod
    def _step_stop_first(instance: Instance, strategy):
        for delta, action, *args in strategy(instance):
            if delta > 0:
                action(*args)
                return delta
        return None

    @staticmethod
    def _step_greed(instance: Instance, strategy):
        best_delta = 0
        next_action = None
        next_args = None
        for delta, action, *args in strategy(instance):
            if delta > best_delta:
                best_delta = delta
                next_action = action
                next_args = args

        if best_delta > 0:
            next_action(*next_args)
            return best_delta
        else:
            return None

    def solve(self, instance):
        instance = instance.copy()

        strategy = [self._strategy_1, self._strategy_2][self._strategy_id]
        step = [self._step_greed, self._step_stop_first][self._step_id]

        for i in range(self._step_number):
            res = step(instance, strategy)
            if res is None:
                break

        return instance


def test1():
    graph = hw_2.CompleteGraphGen.generate(10)
    instance = Instance(graph)

    base = BaseSolver()
    base.solve(instance)

    hw2_solver = hw_2.CliquePartitioningProblem(graph)
    true_solution = hw2_solver.solve()
    instance_2 = Instance(graph, true_solution)

    print(f"obj: {instance.obj_value()}")
    print(f"true obj: {instance_2.obj_value()}")


def test2():
    graph = hw_2.CompleteGraphGen.generate(10)
    instance = Instance(graph)

    base = BaseSolver()
    base.solve(instance)

    ls = LocalSearch()
    instance_2 = ls.solve(instance, 10, 0, 0)

    hw2_solver = hw_2.CliquePartitioningProblem(graph)
    true_solution = hw2_solver.solve()
    instance_3 = Instance(graph, true_solution)

    print(f"obj: {instance.obj_value()}")
    print(f"obj: {instance_2.obj_value()}")
    print(f"true_solution: {instance_3.obj_value()}")


def main_test():
    # (0, 0) - ((a,b)  , greed     ),
    # (0, 1) - ((a,b)  , first_stop),
    # (1, 0) - ((a,b,c), greed     ),
    # (1, 1) - ((a,b,c), first_stop),

    # нужно (0, 0) VS (1, 0)    и    (1, 0) VS (1, 1)
    def temp_def(a1, a2):
        dtimes = np.array([0.0, 0.0])
        ds = np.array([0.0, 0.0])
        n = 50
        for test_number in range(n):
            graph = hw_2.CompleteGraphGen.generate(50)
            instance = Instance(graph)
            base = BaseSolver()
            base.solve(instance)
            s1 = instance.obj_value()

            ls = LocalSearch(10, *a1)
            st = time.time()
            instance_2 = ls.solve(instance)
            p1 = time.time()

            ls = LocalSearch(1, *a2)
            p2 = time.time()
            instance_3 = ls.solve(instance)
            fn = time.time()

            dtimes += (p1 - st, fn - p2)

            ds += (instance_2.obj_value() - s1, instance_3.obj_value() - s1)
        dtimes /= n
        print(f"{a1} VS {a2} time: {dtimes}")
        print(f"{a1} VS {a2} obj: {ds}")

    temp_def((0, 0), (1, 0))
    temp_def((1, 0), (1, 1))
    # time - затраченное время, obj - насколько учлучшилась функция после LS
    # (0, 0) VS (1, 0) time: [0.09311929 0.82128852]
    # (0, 0) VS (1, 0) obj: [15404.55328308 15594.92377154]
    # Видно, что в среднем (0, 0) работает быстрее, причем улучшает в среднем примерно так же как (1, 0)
    # Итого, берем ((a,b), greed)

    # (1, 0) VS (1, 1) time: [0.8310325  0.11410839]
    # (1, 0) VS (1, 1) obj: [15174.54810291 15753.84239695]
    # Здесь вариант (1, 1) работает чуть быстее, причем улучшает в среднем чуть лучше, чем (1, 0)
    # Итого, ((a,b,c), first_stop) чуть лучше


if __name__ == "__main__":
    main_test()
