"""Rules engine for show order scheduling validation and scoring."""

from typing import Tuple, List, Dict


class RulesEngine:
    """Validates and scores permutation assignments against scheduling rules."""

    def __init__(self, performers: List[str], objects: List[str], run_history: List[Dict] = None):
        """
        Initialize rules engine with optional run history for context.
        
        Args:
            performers: List of performer names (excluding "None")
            objects: List of object names
            run_history: List of dicts like {"Domin": (obj, performer), "Alquist": (obj, performer)}
        """
        self.performers = [p for p in performers if p != "None"]
        self.objects = objects
        self.run_history = run_history or []
        self._init_counts()

    def _init_counts(self) -> None:
        """Initialize performer counts for characters and objects."""
        self.char_counts = {
            performer: {"Domin": 0, "Alquist": 0}
            for performer in self.performers
        }
        self.obj_counts = {
            performer: {obj: 0 for obj in self.objects}
            for performer in self.performers
        }
        for run in self.run_history:
            self._apply_counts(run["Domin"], "Domin")
            self._apply_counts(run["Alquist"], "Alquist")

    def _apply_counts(self, perm: Tuple[str, str], position: str) -> None:
        """Apply a permutation to counts (ignores performer None)."""
        obj, performer = perm
        if performer == "None":
            return
        if performer not in self.char_counts:
            return
        self.char_counts[performer][position] += 1
        if obj in self.obj_counts[performer]:
            self.obj_counts[performer][obj] += 1

    def rule1_no_same_performer_both_positions(
        self, domin_perm: Tuple[str, str], alquist_perm: Tuple[str, str]
    ) -> bool:
        """
        Rule 1: No same performer in both positions in same run.
        
        Args:
            domin_perm: (object, performer) tuple for Domin position
            alquist_perm: (object, performer) tuple for Alquist position
        
        Returns:
            True if valid (different performers), False if violation
        """
        domin_obj, domin_perf = domin_perm
        alquist_obj, alquist_perf = alquist_perm
        
        if domin_perf == "None" or alquist_perf == "None":
            return True
        
        return domin_perf != alquist_perf

    def rule2_no_same_object_both_positions(
        self, domin_perm: Tuple[str, str], alquist_perm: Tuple[str, str]
    ) -> bool:
        """
        Rule 2: No same object in both positions in same run.
        
        Args:
            domin_perm: (object, performer) tuple for Domin position
            alquist_perm: (object, performer) tuple for Alquist position
        
        Returns:
            True if valid (different objects), False if violation
        """
        domin_obj, _ = domin_perm
        alquist_obj, _ = alquist_perm
        
        return domin_obj != alquist_obj

    def rule3_no_same_object_consecutive_runs(
        self, position: str, proposed_obj: str
    ) -> bool:
        """
        Rule 3: No same object in same position across consecutive runs.
        
        Args:
            position: "Domin" or "Alquist"
            proposed_obj: Object name being proposed for current run
        
        Returns:
            True if valid (not same as last run), False if violation
        """
        if not self.run_history:
            return True
        
        last_run = self.run_history[-1]
        last_obj, _ = last_run[position]
        
        return proposed_obj != last_obj

    def rule4_consecutive_object_same_performer(
        self, position: str, proposed_perm: Tuple[str, str]
    ) -> bool:
        """
        Rule 4: If an object appears in consecutive runs but switches positions,
        the performer must stay the same.

        Example:
        - Run N: Alquist = Shirt, Moose
        - Run N+1: Domin = Shirt, Moose  ✅
        - Run N+1: Domin = Shirt, Luca   ❌
        """
        if not self.run_history:
            return True

        last_run = self.run_history[-1]
        other_position = "Alquist" if position == "Domin" else "Domin"

        last_obj, last_perf = last_run[other_position]
        proposed_obj, proposed_perf = proposed_perm

        if proposed_obj == last_obj:
            return proposed_perf == last_perf

        return True

    def all_hard_rules(
        self, domin_perm: Tuple[str, str], alquist_perm: Tuple[str, str], position_being_checked: str = None
    ) -> Tuple[bool, str]:
        """
        Check all hard rules.
        
        Args:
            domin_perm: (object, performer) for Domin
            alquist_perm: (object, performer) for Alquist
            position_being_checked: Optional position to check Rule 3 context
        
        Returns:
            (is_valid, violation_message) tuple
        """
        if not self.rule1_no_same_performer_both_positions(domin_perm, alquist_perm):
            return False, "Rule 1: Same performer in both positions"
        
        if not self.rule2_no_same_object_both_positions(domin_perm, alquist_perm):
            return False, "Rule 2: Same object in both positions"
        
        domin_obj, _ = domin_perm
        alquist_obj, _ = alquist_perm
        if not self.rule3_no_same_object_consecutive_runs("Domin", domin_obj):
            return False, "Rule 3: Domin object same as previous run"
        if not self.rule3_no_same_object_consecutive_runs("Alquist", alquist_obj):
            return False, "Rule 3: Alquist object same as previous run"

        if not self.rule4_consecutive_object_same_performer("Domin", domin_perm):
            return False, "Rule 4: Domin object switched from other position with different performer"
        if not self.rule4_consecutive_object_same_performer("Alquist", alquist_perm):
            return False, "Rule 4: Alquist object switched from other position with different performer"
        
        return True, ""

    def rule4_gap_preference(
        self, perm: Tuple[str, str], position: str
    ) -> int:
        """
        Rule 4: Prefer gap of 2+ between same (object, performer) pair in same position.
        
        Args:
            perm: (object, performer) tuple
            position: "Domin" or "Alquist"
        
        Returns:
            Score: 100 (gap>=2), 50 (gap==1), 10 (gap==0 but unavoidable)
        """
        if not self.run_history:
            return 100
        
        for i in range(len(self.run_history) - 1, -1, -1):
            if self.run_history[i][position] == perm:
                gap = len(self.run_history) - 1 - i
                if gap >= 2:
                    return 100
                elif gap == 1:
                    return 50
                else:
                    return 10
        
        return 100

    def _balance_penalty(self, domin_perm: Tuple[str, str], alquist_perm: Tuple[str, str]) -> int:
        temp_char = {
            performer: self.char_counts[performer].copy()
            for performer in self.performers
        }
        temp_obj = {
            performer: self.obj_counts[performer].copy()
            for performer in self.performers
        }

        for position, perm in ("Domin", domin_perm), ("Alquist", alquist_perm):
            obj, performer = perm
            if performer == "None" or performer not in temp_char:
                continue
            temp_char[performer][position] += 1
            if obj in temp_obj[performer]:
                temp_obj[performer][obj] += 1

        penalty = 0
        for performer in self.performers:
            dom_count = temp_char[performer]["Domin"]
            alq_count = temp_char[performer]["Alquist"]
            penalty += abs(dom_count - alq_count) * 5

            obj_counts = temp_obj[performer]
            if obj_counts:
                max_count = max(obj_counts.values())
                min_count = min(obj_counts.values())
                penalty += (max_count - min_count)

        return penalty

    def _intermission_pair_penalty(
        self,
        domin_perm: Tuple[str, str],
        alquist_perm: Tuple[str, str],
        last_intermission_pair_performer: str | None,
        is_after_intermission: bool,
        animatronic_perm: Tuple[str, str] | None,
    ) -> int:
        if not is_after_intermission or not animatronic_perm:
            return 0
        if last_intermission_pair_performer is None:
            return 0

        anim_obj, anim_perf = animatronic_perm
        if (domin_perm[0], domin_perm[1]) == (anim_obj, anim_perf):
            other_perf = alquist_perm[1]
        elif (alquist_perm[0], alquist_perm[1]) == (anim_obj, anim_perf):
            other_perf = domin_perm[1]
        else:
            return 0

        if other_perf == last_intermission_pair_performer:
            return 25

        return 0

    def score_permutation(
        self,
        domin_perm: Tuple[str, str],
        alquist_perm: Tuple[str, str],
        last_intermission_pair_performer: str | None = None,
        is_after_intermission: bool = False,
        animatronic_perm: Tuple[str, str] | None = None,
    ) -> int:
        """
        Score a permutation pair based on soft rules.
        
        Returns:
            Higher is better. Combines gap preference and balance penalty.
        """
        domin_score = self.rule4_gap_preference(domin_perm, "Domin")
        alquist_score = self.rule4_gap_preference(alquist_perm, "Alquist")
        gap_score = (domin_score + alquist_score) // 2

        balance_penalty = self._balance_penalty(domin_perm, alquist_perm)
        intermission_penalty = self._intermission_pair_penalty(
            domin_perm,
            alquist_perm,
            last_intermission_pair_performer,
            is_after_intermission,
            animatronic_perm,
        )

        return (gap_score * 10) - balance_penalty - intermission_penalty

    def record_run(self, domin_perm: Tuple[str, str], alquist_perm: Tuple[str, str]) -> None:
        """
        Record a run assignment in history for future constraint checks.
        
        Args:
            domin_perm: (object, performer) for Domin
            alquist_perm: (object, performer) for Alquist
        """
        self.run_history.append({
            "Domin": domin_perm,
            "Alquist": alquist_perm,
        })
        self._apply_counts(domin_perm, "Domin")
        self._apply_counts(alquist_perm, "Alquist")

    def reset(self) -> None:
        """Reset run history (for new segment)."""
        self.run_history = []
        self._init_counts()
