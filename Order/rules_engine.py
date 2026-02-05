"""Rules engine for show order scheduling validation and scoring."""

from typing import Tuple, List, Dict


class RulesEngine:
    """Validates and scores permutation assignments against scheduling rules."""

    def __init__(self, run_history: List[Dict] = None):
        """
        Initialize rules engine with optional run history for context.
        
        Args:
            run_history: List of dicts like {"Domin": (obj, performer), "Alquist": (obj, performer)}
        """
        self.run_history = run_history or []

    # HARD RULES (violations = reject immediately)

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
        
        # If either is "None" performer, allow it
        if domin_perf == "None" or alquist_perf == "None":
            return True
        
        # Performers must be different
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
        
        # Objects must be different
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
            return True  # First run, always valid
        
        last_run = self.run_history[-1]
        last_obj, _ = last_run[position]
        
        # Objects must be different between consecutive runs
        return proposed_obj != last_obj

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
        # Rule 1
        if not self.rule1_no_same_performer_both_positions(domin_perm, alquist_perm):
            return False, "Rule 1: Same performer in both positions"
        
        # Rule 2
        if not self.rule2_no_same_object_both_positions(domin_perm, alquist_perm):
            return False, "Rule 2: Same object in both positions"
        
        # Rule 3
        domin_obj, _ = domin_perm
        alquist_obj, _ = alquist_perm
        if not self.rule3_no_same_object_consecutive_runs("Domin", domin_obj):
            return False, "Rule 3: Domin object same as previous run"
        if not self.rule3_no_same_object_consecutive_runs("Alquist", alquist_obj):
            return False, "Rule 3: Alquist object same as previous run"
        
        return True, ""

    # SOFT RULES (violations = lower preference score)

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
            return 100  # First occurrence, perfect score
        
        # Search backwards through history for this permutation in this position
        for i in range(len(self.run_history) - 1, -1, -1):
            if self.run_history[i][position] == perm:
                gap = len(self.run_history) - 1 - i
                if gap >= 2:
                    return 100
                elif gap == 1:
                    return 50
                else:  # gap == 0 (shouldn't happen if hard rules pass)
                    return 10
        
        # Never used before, best score
        return 100

    def score_permutation(
        self, domin_perm: Tuple[str, str], alquist_perm: Tuple[str, str]
    ) -> int:
        """
        Score a permutation pair based on soft rules.
        
        Args:
            domin_perm: (object, performer) for Domin
            alquist_perm: (object, performer) for Alquist
        
        Returns:
            Combined score (higher is better)
        """
        domin_score = self.rule4_gap_preference(domin_perm, "Domin")
        alquist_score = self.rule4_gap_preference(alquist_perm, "Alquist")
        
        # Average the scores
        return (domin_score + alquist_score) // 2

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

    def reset(self) -> None:
        """Reset run history (for new segment)."""
        self.run_history = []
