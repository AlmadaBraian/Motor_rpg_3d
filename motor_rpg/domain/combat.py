from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Protocol

from motor_rpg.domain.config import CombatConfig


class RollProvider(Protocol):
    def randint(self, low: int, high: int) -> int: ...


@dataclass(frozen=True, slots=True)
class ActorStats:
    name: str = ""

    speed: int = 5

    accuracy: int = 0
    evasion: int = 0

    attack_bonus: int = 0
    armor_class: int = 10

    damage_min: int = 4
    damage_max: int = 10

    defense: int = 0

    critical_chance: float = 5.0

    body_type: str = "normal"


@dataclass(frozen=True, slots=True)
class CombatResult:
    hit: bool
    critical_hit: bool
    result: str
    damage: int
    roll: int
    attack_total: int
    armor_class: float


class CombatRules:
    """Deterministic, testable tactical-combat rules.

    Runtime classes pass actor definitions and an injected RNG here instead of
    recalculating combat math inline. The rules intentionally stay free of Tk,
    OpenGL, scene or animation state.
    """

    def __init__(self, config: CombatConfig | None = None, rng: RollProvider | None = None) -> None:
        self.config = config or CombatConfig()
        self.rng = rng or Random()

    def resolve_attack(
    self,
    attacker: ActorStats,
    target: ActorStats,
    attacker_runtime=None,
    *,
    target_guarding=False,
    ) -> CombatResult:
        body_scale = self.config.body_type_armor_scale.get(target.body_type, 1.0)
        armor_class = target.armor_class * body_scale
        if target_guarding:
            armor_class += self.config.guard_armor_bonus

        attack_multiplier = (
            self.config.speed_attack_multiplier
            if attacker.speed > self.config.speed_bonus_threshold
            else 1.0
        )
        attack_bonus = round(attacker.attack_bonus * attack_multiplier)

        roll = self.rng.randint(1, self.config.d20_sides)
        attack_total = roll + attack_bonus + attacker.accuracy

        #critical_hit = roll == self.config.natural_critical_hit
        #critical_miss = roll == self.config.natural_critical_miss

        
        hit_chance = (
            85
            + attacker.accuracy
            - target.evasion
        )

        hit_chance = max(10, min(95, hit_chance))

        hit = self.rng.randint(1, 100) <= hit_chance
        
        result = "hit" if hit else "miss"

        damage = 0
        critical_hit = False

        if hit and attacker_runtime:
            critical_hit, attacker_runtime.crit_meter = (
                self.roll_pseudo_random_critical(
                    attacker_runtime.crit_meter,
                    attacker.critical_chance
                )
            )
            damage = self._roll_damage(attacker, target, critical_hit=critical_hit, target_guarding=target_guarding)

            if hit:
                result = "critical" if critical_hit else "hit"
            else:
                result = "miss"

        return CombatResult(
            hit=hit,
            critical_hit=critical_hit,
            result=result,
            damage=damage,
            roll=roll,
            attack_total=attack_total,
            armor_class=armor_class,
        )
    
    def roll_pseudo_random_critical(
        self,
        crit_meter: float,
        crit_chance: float,
    ):
        crit_meter += crit_chance

        critical = False

        if crit_meter >= 100:
            critical = True
            crit_meter -= 100

        return critical, crit_meter

    def _roll_damage(
        self,
        attacker: ActorStats,
        target: ActorStats,
        *,
        critical_hit: bool,
        target_guarding: bool,
    ) -> int:
        dmg_min = max(0, attacker.damage_min)
        dmg_max = max(dmg_min, attacker.damage_max)
        base_damage = self.rng.randint(dmg_min, dmg_max)
        mitigation = 100 / (100 + max(0, target.defense) * 10)
        damage = round(base_damage * mitigation)

        if critical_hit:
            damage *= 2

        if target_guarding:
            damage = round(damage * self.config.guard_damage_multiplier)

        return max(1, damage)


def actor_stats_from_object(name: str, source: object) -> ActorStats:
    """Build typed stats from legacy ActorAsset-like objects."""

    return ActorStats(
        name=name,
        speed=int(getattr(source, "speed", 5)),
        accuracy=int(getattr(source, "accuracy", 0)),
        evasion=int(getattr(source, "evasion", 0)),
        attack_bonus=int(getattr(source, "attack_bonus", 0)),
        armor_class=int(getattr(source, "armor_class", 10)),
        damage_min=int(getattr(source, "damage_min", 4)),
        damage_max=int(getattr(source, "damage_max", 10)),
        defense=int(getattr(source, "defense", 0)),
        critical_chance=float(getattr(source, "critical_chance", 5.0)),
        body_type=str(getattr(source, "body_type", "normal")),
    )
