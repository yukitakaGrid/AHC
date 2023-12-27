from dataclasses import dataclass
from enum import Enum
import sys

MAX_INVEST_LEVEL = 20
NO_SELECT = -1

@dataclass
class Project:
    h: int
    v: int
    c: float


class CardType(Enum):
    WORK_SINGLE = 0
    WORK_ALL = 1
    CANCEL_SINGLE = 2
    CANCEL_ALL = 3
    INVEST = 4


@dataclass
class Card:
    t: CardType
    w: int
    p: int
    c: float


class Judge:

    def __init__(self, n: int, m: int, k: int):
        self.n = n
        self.m = m
        self.k = k

    def read_initial_cards(self) -> list[Card]:
        cards = []
        for _ in range(self.n):
            t, w = map(int, input().split())
            c = w
            if t == CardType.WORK_ALL: #全力労働の場合プロジェクトが多いほど費用対効果があがる
                c *= self.m
            cards.append(Card(CardType(t), w, 0, c))
        return cards

    def read_projects(self) -> list[Project]:
        projects = []
        for _ in range(self.m):
            h, v = map(int, input().split())
            c = v / h
            projects.append(Project(h, v, c))
        return projects

    def use_card(self, c: int, m: int) -> None:
        print(f"{c} {m}", flush=True)

    def read_money(self) -> int:
        return int(input())

    def read_next_cards(self) -> list[Card]:
        cards = []
        for _ in range(self.k):
            t, w, p = map(int, input().split())
            c = w / (p+1)
            if t == CardType.WORK_ALL: #全力労働の場合プロジェクトが多いほど費用対効果があがる
                c *= self.m
            cards.append(Card(CardType(t), w, p, c))
        return cards

    def select_card(self, r: int) -> None:
        print(r, flush=True)

    def comment(self, message: str) -> None:
        print(f"# {message}")


class Solver:

    def __init__(self, n: int, m: int, k: int, t: int):
        self.n = n
        self.m = m
        self.k = k
        self.t = t
        self.judge = Judge(n, m, k)
        self.low_value_thresh = 0.5
        self.low_value_all_thresh = m*0.5

    def solve(self) -> int:
        self.turn = 0
        self.money = 0
        self.invest_level = 0
        self.cards = self.judge.read_initial_cards()
        self.projects = self.judge.read_projects()

        for _ in range(self.t):
            use_card_i, use_target = self._select_action()
            if self.cards[use_card_i].t == CardType.INVEST:
                self.invest_level += 1
            # example for comments
            self.judge.comment(f"used {self.cards[use_card_i]} to target {use_target}")
            self.judge.use_card(use_card_i, use_target)
            assert self.invest_level <= MAX_INVEST_LEVEL

            self.projects = self.judge.read_projects()
            self.money = self.judge.read_money()

            next_cards = self.judge.read_next_cards()
            select_card_i = self._select_next_card(next_cards)
            self.cards[use_card_i] = next_cards[select_card_i]
            self.judge.select_card(select_card_i)
            self.money -= next_cards[select_card_i].p
            assert self.money >= 0

            self.turn += 1

        return self.money

    def _select_action(self) -> tuple[int, int]:
        #使用カード選択
        max_cost = -1
        select_c = 0
        #プロジェクトの価値の度合いを計算
        select_high_cost_p = NO_SELECT #-1の場合高いコストなし、それ以外の場合変えるべきプロジェクトあり
        high_cost_all = 0 #1の場合全体的にコストが高い
        cost_sum = 0.0
        for i in range(self.m):
            c = self.projects[i].c
            if self.low_value_thresh > c:
                select_high_cost_p = i
            
            cost_sum += c

            if self.low_value_all_thresh > cost_sum:
                high_cost_all = 1

        for i in range(self.n):
            if((high_cost_all == 1) & (self.cards[i].t == CardType.CANCEL_ALL)): #条件を満たしていれば最優先的に業務転換カードを選択
                select_c = i
                break
                
            elif((select_high_cost_p != NO_SELECT) & (self.cards[i].t == CardType.CANCEL_SINGLE)): #条件を満たしていれば優先的にキャンセルカードを選択
                select_c = i
                break

            elif self.cards[i].t == CardType.INVEST: #増資カードがあれば優先的に使用
                select_c = i
                break

            elif((max_cost<self.cards[i].c) & self.card_is_work(i)): #費用対効果の高い労働カードを選択
                max_cost = self.cards[i].c
                select_c = i
        
        #プロジェクト選択
        #労働力と残務量が近いカードを選択
        diff = sys.maxsize
        select_p = 0

        #プロジェクト選択と関係ない場合の処理
        if(self.cards[select_c].t == CardType.CANCEL_ALL):
            select_p = 0

        elif(self.cards[select_c].t == CardType.INVEST):
            select_p = 0

        elif(self.cards[select_c].t == CardType.WORK_ALL):
            select_p = 0

        #プロジェクト選択と関係ある場合の処理
        elif(self.cards[select_c].t == CardType.CANCEL_SINGLE):
            select_p = select_high_cost_p

        elif(self.cards[select_c].t == CardType.WORK_SINGLE):
            for i in range(self.m): #カードの労働力とプロジェクトの残務量の差が一番少ないプロジェクトを選択
                if((diff>(self.projects[i].h - self.cards[select_c].w)*(self.projects[i].h - self.cards[select_c].w))):
                    diff = (self.projects[i].h - self.cards[select_c].w)*(self.projects[i].h - self.cards[select_c].w)
                    select_p = i
        
        return (select_c, select_p)

    def _select_next_card(self, next_cards: list[Card]) -> int:
        #プロジェクトの価値の度合いを計算
        select_high_cost_p = NO_SELECT #-1の場合高いコストなし、それ以外の場合変えるべきプロジェクトあり
        high_cost_all = 0 #1の場合全体的にコストが高い
        cost_sum = 0.0
        for i in range(self.m):
            c = self.projects[i].c
            if self.low_value_thresh > c:
                select_high_cost_p = i
            
            cost_sum += c

            if self.low_value_all_thresh > cost_sum:
                high_cost_all = 1

        max_cost = -1
        select_c = 0
        for i in range(self.k):
            if(self.money>next_cards[i].p):
                if((high_cost_all == 1) & (next_cards[i].t == CardType.CANCEL_ALL)): #条件を満たしていれば最優先的に業務転換カードを選択
                    select_c = i
                    break
                    
                elif((select_high_cost_p != NO_SELECT) & (next_cards[i].t == CardType.CANCEL_SINGLE)): #条件を満たしていれば優先的にキャンセルカードを選択
                    select_c = i
                    break

                elif next_cards[i].t == CardType.INVEST:
                    select_c = i
                    break

                elif(max_cost<next_cards[i].c) & ((next_cards[i].t == CardType.WORK_SINGLE) | (next_cards[i].t == CardType.WORK_ALL)):
                    max_cost = next_cards[i].c
                    select_c = i
        return select_c
    
    def card_is_work(self,i):
        return (self.cards[i].t == CardType.WORK_SINGLE) | (self.cards[i].t == CardType.WORK_ALL)


def main():
    n, m, k, t = map(int, input().split())
    solver = Solver(n, m, k, t)
    score = solver.solve()
    print(f"score:{score}", file=sys.stderr)


if __name__ == "__main__":
    main()
