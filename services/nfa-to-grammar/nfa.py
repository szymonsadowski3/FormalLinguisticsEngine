from typing import Any, Dict, FrozenSet, List, Set, Tuple
from itertools import combinations
import json
import copy


DEAD_STATE = "qdead"


class NFA():
    """
        Non-deterministic finite automaton.

        All operations over automata are implemented here, this class
        represents a NFA although it can be deterministic. The transition
        function (delta) is represented as a dictionary that maps
        (state, symbol) -> Set[state], it is deterministic if all transitions
        take to only one state.
    """

    def __init__(
            self,
            states: Set[str]=None,
            alphabet: Set[str]=None,
            transitions: Dict[Tuple[str, str], Set[str]]=None,
            initial_state: str="",
            final_states: Set[str]=None) -> None:
        self._states = states if states else set()
        self._alphabet = alphabet if alphabet else set()
        self._transitions = transitions if transitions else {}
        self._initial_state = initial_state
        self._final_states = final_states if final_states else set()

    @property
    def states(self) -> List[str]:
        """ Returns an ordered list of states """
        return [self._initial_state] + \
            sorted(self._states - {self._initial_state})

    @property
    def alphabet(self) -> List[str]:
        """ Returns an ordered list of symbols """
        return sorted(self._alphabet)

    @property
    def transition_table(self) -> Dict[Tuple[str, str], Set[str]]:
        """ Returns the transition function, a dictionary """
        return self._transitions

    @property
    def initial_state(self) -> str:
        """ Returns the initial state """
        return self._initial_state

    @property
    def final_states(self) -> Set[str]:
        """ Returns the set of final states """
        return self._final_states

    def add_state(self, state: str) -> None:
        """ Adds a state """
        if not self._initial_state:
            self._initial_state = state
        self._states.add(state)

    def remove_state(self, state: str) -> None:
        """ Removes a state """
        # may not remove initial state
        if state != self._initial_state:
            self._states.discard(state)
            self._final_states.discard(state)

            for symbol in self._alphabet:
                # remove useless transitions that come from the removed state
                if (state, symbol) in self._transitions:
                    del self._transitions[state, symbol]

            empty_transitions = set()  # type Set[Tuple[str, str]]
            for actual_state, next_state in self._transitions.items():
                # remove transitions that go to the removed state
                next_state.discard(state)
                if not next_state:
                    empty_transitions.add(actual_state)

            for transition in empty_transitions:
                del self._transitions[transition]

    def toggle_final_state(self, state: str) -> None:
        """ Toggle a state to be final or not """
        if state in self._states:
            if state in self._final_states:
                self._final_states.remove(state)
            else:
                self._final_states.add(state)

    def add_symbol(self, symbol: str) -> None:
        """ Adds a symbol """
        self._alphabet.add(symbol)

    def remove_symbol(self, symbol: str) -> None:
        """ Removes a symbol """
        self._alphabet.discard(symbol)
        for state in self._states:
            # remove transitions by the removed symbol
            if (state, symbol) in self._transitions:
                del self._transitions[state, symbol]

    def set_transition(
            self, state: str, symbol: str, next_states: Set[str]) -> None:
        """ Set the transition function for a given state and symbol """
        if not next_states:
            # assert transition won't exist
            self._transitions.pop((state, symbol), set())
        elif next_states <= self._states:
            self._transitions[state, symbol] = next_states
        else:
            states = ", ".join(next_states - self._states)
            raise KeyError("State(s) {} do not exist".format(states))

    def accept(self, string: str) -> bool:
        """
            Checks if a given string is member of the language recognized by
            the NFA. Using non-deterministic transitions.
        """
        current_state = {self._initial_state}

        for symbol in string:
            next_state = set()  # type Set[str]
            for state in current_state:
                next_state.update(
                    self._transitions.get((state, symbol), set()))
            current_state = next_state

        return bool(current_state.intersection(self._final_states))

    def minimize(self) -> None:
        """
            Transforms the automaton in the correspondent minimal automaton,
            that is, without dead, unreachable and equivalent states
        """
        if not self.is_deterministic():
            raise RuntimeError("Automata is non-deterministic")

        self.remove_unreachable()
        self.remove_dead()
        self.merge_equivalent()

    def remove_unreachable(self) -> None:
        """ Removes the states that the automaton will never be in """
        reachable = set()  # type: Set[str]
        new_reachable = {self._initial_state}
        while not new_reachable <= reachable:
            reachable |= new_reachable
            new_reachable_copy = new_reachable.copy()
            new_reachable = set()
            for state in new_reachable_copy:
                for symbol in self._alphabet:
                    new_reachable.update(
                        self._transitions.get((state, symbol), set()))

        for unreachable_state in self._states - reachable:
            self.remove_state(unreachable_state)

    def remove_dead(self) -> None:
        """ Removes states that never reach a final state """
        alive = set()  # type: Set[str]
        new_alive = self._final_states.copy()
        while not new_alive <= alive:
            alive |= new_alive
            new_alive = set()
            for (state, _), next_states in self._transitions.items():
                if any(next_state in alive for next_state in next_states):
                    new_alive.add(state)

        for dead_state in self._states - alive:
            self.remove_state(dead_state)

    def merge_equivalent(self) -> None:
        """ Merges equivalent states """
        if not self.is_deterministic():
            raise RuntimeError("Automata is non-deterministic")

        # pairs of undistinguishable states
        undistinguishable = set()  # type: Set[FrozenSet[str]]

        # initially, you can't distinguish final and non-final states
        for pair in combinations(self._states - self._final_states, 2):
            undistinguishable.add(frozenset(pair))
        for pair in combinations(self._final_states, 2):
            undistinguishable.add(frozenset(pair))

        # find new distinguishable states
        while True:
            new_distinguishable_found = False
            undistinguishable_copy = undistinguishable.copy()
            for state_a, state_b in undistinguishable_copy:
                if not self._are_undistinguishable(
                        state_a, state_b, undistinguishable_copy):
                    undistinguishable.remove(frozenset((state_a, state_b)))
                    new_distinguishable_found = True
            if not new_distinguishable_found:
                break

        for state_a, state_b in undistinguishable:
            self._merge_states(state_a, state_b)

    def _are_undistinguishable(
            self, state_a: str, state_b: str,
            undistinguishable: Set[FrozenSet[str]]) -> bool:
        """
            State a and b are distinguishable if they go to distinguishable
            states for some input symbol.
        """
        for symbol in self._alphabet:
            transition_a = \
                list(self._transitions.get((state_a, symbol), {""}))[0]
            transition_b = \
                list(self._transitions.get((state_b, symbol), {""}))[0]
            if transition_a != transition_b and \
                    frozenset((transition_a, transition_b)) not in \
                    undistinguishable:
                return False
        return True

    def _merge_states(self, state_a: str, state_b: str):
        """ Merges state b into a, making them one state """
        state_to_be_removed = state_b
        state_to_be_kept = state_a
        # avoid removing the initial state or one that's already removed
        if state_to_be_removed == self._initial_state or \
                state_to_be_kept not in self._states:
            state_to_be_removed = state_a
            state_to_be_kept = state_b

        for actual_state, next_state in self._transitions.items():
            if next_state == {state_to_be_removed}:
                self._transitions[actual_state] = {state_to_be_kept}
        self.remove_state(state_to_be_removed)

    def determinize(self) -> None:
        """
            Given the actual NFA, determinizes it, appending the new
            transitions and states to the actual ones of the NFA.
        """
        original_transitions = self._transitions.copy()

        # create necessary states
        for next_state in original_transitions.values():
            if len(next_state) > 1:
                self._determinize_state(next_state)

        # rewrite transitions
        self._transitions = {
            actual: {"".join(sorted(next_state))}
            for actual, next_state in self._transitions.items()
        }

        self.remove_unreachable()

    def _determinize_state(self, states_set: Set[str]) -> None:
        """
            For a given set of states, verify whether they pertains to the
            actual states of the FA. In negative case, add it and insert
            the transitions properly
        """
        name = "".join(sorted(states_set))
        if name and name not in self._states:
            self.add_state(name)
            if states_set.intersection(self._final_states):
                self._final_states.add(name)
            for symbol in self._alphabet:
                reachable = self._find_reachable(states_set, symbol)
                if reachable:
                    self._transitions[name, symbol] = reachable
                    self._determinize_state(reachable)

    def _find_reachable(self, states: Set[str], symbol: str) -> Set[str]:
        """
            Given a set of states, applies a depth search algorithm
            to find the reachable states of them through transitions of the
            given symbol
        """
        found = set()  # type: Set[str]
        for state in states:
            if (state, symbol) in self._transitions:
                found.update(self._transitions[state, symbol])
        return found

    def is_deterministic(self) -> bool:
        """ Checks if the automaton is deterministic """
        return all(
            len(transition) == 1 for transition in self._transitions.values())

    def is_empty(self) -> bool:
        """ Checks if the language defined by the automaton is empty """
        nfa = copy.deepcopy(self)
        nfa.remove_unreachable()
        return len(nfa.final_states) == 0

    def is_finite(self) -> bool:
        """ Checks if the language defined by the automaton is finite """
        nfa = copy.deepcopy(self)
        nfa.remove_dead()
        return not nfa._has_recursion(self._initial_state, set())

    def _has_recursion(self, to_visit: str, visited: Set[str]) -> bool:
        """
            Checks if the automata has recursive states, using a depth
            first search approach.
        """
        if to_visit in visited:
                return True

        visited.add(to_visit)
        reachable = set()  # type: Set[str]

        # Find the reachable through all symbols
        for symbol in self._alphabet:
            reachable.update(self._find_reachable({to_visit}, symbol))

        for state in reachable:
            if self._has_recursion(state, copy.deepcopy(visited)):
                return True

        return False

    def beautify_qn(self, begin_at: int=0) -> None:
        """ Transforms all states to q1,q2,...,qn """
        beautiful_states = {self._initial_state: "q" + str(begin_at)}

        beautiful_states.update({
            state: "q" + str(begin_at + number + 1) for number, state in
            enumerate(sorted(self._states - {self._initial_state}))})

        self._beautify(beautiful_states)

    def beautify_abc(self) -> None:
        """ Transforms all states to S,A,B,...,Z """
        if len(self._states) > 26:
            raise RuntimeError("Too many states")

        beautiful_states = {self._initial_state: "S"}
        number = 0
        for state in sorted(self._states - {self._initial_state}):
            beautiful_states[state] = chr(ord('A') + number)
            if number == 17:  # skip "S", the initial state
                number += 1
            number += 1
        self._beautify(beautiful_states)

    def _beautify(self, beautiful_states: Dict[str, str]) -> None:
        self._initial_state = beautiful_states[self._initial_state]
        self._states = set(beautiful_states.values())

        self._transitions = {
            (beautiful_states[actual_state], symbol):
            {beautiful_states[state] for state in value}
            for (actual_state, symbol), value in self._transitions.items()
        }

        self._final_states = {
            beautiful_states[state] for state in self._final_states
        }

    def union(self, automaton: 'NFA') -> None:
        """
            Makes the union of two automata, without epsilon transitions,
            and saves it on the actual object.
        """
        self._alphabet.update(automaton._alphabet)
        self._complete()
        self.beautify_qn()

        automaton._alphabet.update(self._alphabet)
        automaton._complete()
        automaton.beautify_qn(len(self._states))

        new_state = "qinitial"
        self._states.add(new_state)

        # Merge states
        self._states.update(automaton._states)
        self._final_states.update(automaton._final_states)
        self._transitions.update(automaton._transitions)
        if any(
                initial_state in self._final_states
                for initial_state in
                {self._initial_state, automaton._initial_state}):
            self._final_states.add(new_state)

        # Creates transitions of the new initial state
        for symbol in self._alphabet:
            self.set_transition(
                new_state, symbol,
                self._transitions.get(
                    (self._initial_state, symbol), set()) |
                automaton.transition_table.get(
                    (automaton._initial_state, symbol), set()))

        self._initial_state = new_state

    def complement(self) -> None:
        """
            Finds the automaton which recognizes the language that is the
            complement of the actual automaton
        """
        self.determinize()
        self._complete()
        for state in self._states:
            self.toggle_final_state(state)

    def intersection(self, automaton: 'NFA') -> None:
        """
            Finds the automaton which recognizes the language that is the
            intersection of the actual automaton with the given one.
        """
        automaton.complement()
        self.complement()
        self.union(automaton)
        self.complement()

    def contains(self, automaton: 'NFA') -> bool:
        """
            Checks if the actual automaton contains another one.
        """
        first_nfa = copy.deepcopy(self)
        second_nfa = copy.deepcopy(automaton)
        first_nfa.complement()
        second_nfa.intersection(first_nfa)
        return second_nfa.is_empty()

    def is_equal(self, automaton: 'NFA') -> bool:
        """
            Checks if two automata are equivalent.
        """
        return self.contains(automaton) and automaton.contains(self)

    def _complete(self) -> None:
        self.add_state(DEAD_STATE)
        for state in self._states:
            for symbol in self._alphabet:
                if (state, symbol) not in self._transitions:
                    self._transitions[state, symbol] = {DEAD_STATE}

    @staticmethod
    def from_regular_grammar(grammar) -> 'NFA':
        """ Converts RegularGrammar to NFA """
        initial_symbol = grammar.initial_symbol()
        productions = grammar.productions()

        states = set(productions.keys()) | {"X"}
        alphabet = set()  # type: Set[str]
        transitions = {}  # type: Dict[Tuple[str, str], Set[str]]
        initial_state = initial_symbol
        final_states = set("X") | \
            ({initial_symbol} if "&" in productions[initial_symbol] else set())

        for non_terminal, prods in productions.items():
            for production in prods:
                if production == "&":
                    continue

                new_transition = "X" if len(production) == 1 else production[1]
                transitions.setdefault(
                    (non_terminal, production[0]), set()).add(new_transition)

                alphabet.add(production[0])

        return NFA(states, alphabet, transitions, initial_state, final_states)

    def save(self, path: str) -> None:
        """ Saves the automaton to a JSON file """
        data = {}  # type: Dict[str, Any]
        data["states"] = sorted(self._states)
        data["alphabet"] = sorted(self._alphabet)
        data["transitions"] = \
            [(k[0], k[1], sorted(v)) for k, v in self._transitions.items()]
        data["initial_state"] = self._initial_state
        data["final_states"] = sorted(self._final_states)
        with open(path, 'w') as automata_file:
            json.dump(data, automata_file, indent=4)

    @staticmethod
    def load(data: dict) -> 'NFA':
        """ Loads the automaton from a JSON file """
        states = set(data["states"])
        alphabet = set(data["alphabet"])
        transitions = {(v[0], v[1]): set(v[2]) for v in data["transitions"]}
        initial_state = data["initial_state"]
        final_states = set(data["final_states"])
        return NFA(
            states, alphabet, transitions, initial_state, final_states)
