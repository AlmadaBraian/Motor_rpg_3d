from __future__ import annotations

from motor_rpg.domain.combat import ActorStats, CombatRules


class FixedRng:
    def __init__(self, *rolls: int) -> None:
        self.rolls = list(rolls)

    def randint(self, low: int, high: int) -> int:
        assert self.rolls
        value = self.rolls.pop(0)
        assert low <= value <= high
        return value


def test_attack_uses_target_armor_and_evasion_for_miss():
    rules = CombatRules(rng=FixedRng(9))
    attacker = ActorStats(name="Hero", accuracy=0, attack_bonus=0)
    target = ActorStats(name="Tank", armor_class=12, evasion=2)

    result = rules.resolve_attack(attacker, target)

    assert result.hit is False
    assert result.result == "miss"
    assert result.attack_total == 9
    assert result.armor_class == 12
    assert result.damage == 0


def test_critical_hit_doubles_mitigated_damage():
    rules = CombatRules(rng=FixedRng(20, 8))
    attacker = ActorStats(name="Hero", damage_min=8, damage_max=8)
    target = ActorStats(name="Slime", defense=0)

    result = rules.resolve_attack(attacker, target)

    assert result.critical_hit is True
    assert result.hit is True
    assert result.damage == 16


def test_guard_increases_armor_and_reduces_damage():
    rules = CombatRules(rng=FixedRng(18, 10))
    attacker = ActorStats(name="Hero", attack_bonus=10, damage_min=10, damage_max=10)
    target = ActorStats(name="Guard", armor_class=10)

    result = rules.resolve_attack(attacker, target, target_guarding=True)

    assert result.hit is True
    assert result.armor_class == 14
    assert result.damage == 6
