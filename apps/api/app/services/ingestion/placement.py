"""Suggest where a submitted dish fits on a learning path.

The path is a ladder of skills: a dish belongs in the earliest stage where the
learner already has (or is just now introduced to) the skills it needs. So:

1. ``needed_stage`` = the highest stage that first teaches any of the dish's skills;
2. difficulty is a SAFETY CEILING: if the dish is much harder than that stage
   (more than one point above the hardest dish there), it moves to the first stage
   that can take it, or to a NEW stage at the end of the path;
3. skills no stage teaches yet are reported as new to the path, for the reviewer.

It only suggests; a person chooses.
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class StageInfo:
    position: int
    title: str
    #: Difficulty score (1-5) of the hardest dish already in the stage.
    max_score: int
    #: Skill slugs taught by the dishes of this stage.
    skills: frozenset[str]


@dataclass(frozen=True)
class Placement:
    stage_position: int
    stage_title: str
    new_stage: bool
    #: Skills of the dish that no stage of the path teaches yet.
    unknown_skills: tuple[str, ...]
    #: Skills first taught at the suggested stage that this dish also uses.
    introduces: tuple[str, ...]
    reason: str


def _first_stage_teaching(skill: str, stages: Sequence[StageInfo]) -> int | None:
    return next((stage.position for stage in stages if skill in stage.skills), None)


def suggest_stage(
    *, score: int, skills: Collection[str], stages: Sequence[StageInfo]
) -> Placement | None:
    """None for a path without stages."""
    if not stages:
        return None
    ordered = sorted(stages, key=lambda stage: stage.position)
    levels = {skill: _first_stage_teaching(skill, ordered) for skill in skills}
    unknown = tuple(skill for skill, level in levels.items() if level is None)
    needed = max(
        (level for level in levels.values() if level is not None), default=ordered[0].position
    )

    reason = f"necesita habilidades que se enseñan hasta la etapa {needed}"
    chosen = next(stage for stage in ordered if stage.position >= needed)
    new_stage = False
    if score > chosen.max_score + 1:
        fitting = next(
            (s for s in ordered if s.position >= needed and score <= s.max_score + 1), None
        )
        if fitting is None:
            new_stage = True
            reason = (
                f"es más difícil (puntaje {score}) que cualquier etapa actual: "
                "conviene una etapa nueva al final"
            )
        else:
            chosen = fitting
            reason = f"su dificultad (puntaje {score}) supera la de las etapas anteriores"

    position = ordered[-1].position + 1 if new_stage else chosen.position
    title = "Nueva etapa" if new_stage else chosen.title
    introduces = tuple(
        skill for skill, level in levels.items() if level is not None and level == position
    )
    if not skills:
        reason = "no se detectaron habilidades; se sugiere según la dificultad"
    return Placement(
        stage_position=position,
        stage_title=title,
        new_stage=new_stage,
        unknown_skills=unknown,
        introduces=introduces,
        reason=reason,
    )
