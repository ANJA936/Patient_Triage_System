"""
Patient Triage System
=====================
Assigns a triage category to a patient based on clinical inputs.

Triage categories (highest to lowest priority):
    - IMMEDIATE  : Life-threatening; requires instant intervention
    - URGENT     : Serious condition; must be seen within 30 minutes
    - NORMAL     : Moderate condition; seen within 2 hours
    - NON-URGENT : Minor condition; can wait or self-care

NOTE: This is an educational model only and NOT a genuine medical
decision-making tool.
"""

from dataclasses import dataclass, field
from typing import List


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

VALID_SYMPTOMS = {
    "chest_pain",
    "difficulty_breathing",
    "unconscious",
    "severe_bleeding",
    "stroke_signs",
    "high_fever",
    "moderate_pain",
    "vomiting",
    "dizziness",
    "minor_cut",
    "mild_headache",
    "none",
}

TRIAGE_LEVELS = ["IMMEDIATE", "URGENT", "NORMAL", "NON-URGENT"]


@dataclass
class Patient:
    """Holds all clinical inputs for a single patient."""

    name: str
    age: int                        # years
    symptoms: List[str]             # list of symptom keys from VALID_SYMPTOMS
    pain_level: int                 # 0–10 (0 = no pain, 10 = worst imaginable)
    fever: float                    # body temperature in °C
    pulse: int                      # beats per minute
    shortness_of_breath: bool       # True / False

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if not self.name or not self.name.strip():
            raise ValueError("Patient name must not be empty.")
        if not (0 <= self.age <= 130):
            raise ValueError(f"Age must be between 0 and 130. Got: {self.age}")
        if not (0 <= self.pain_level <= 10):
            raise ValueError(
                f"Pain level must be between 0 and 10. Got: {self.pain_level}"
            )
        if not (30.0 <= self.fever <= 45.0):
            raise ValueError(
                f"Fever (temperature) must be between 30.0 and 45.0 °C. "
                f"Got: {self.fever}"
            )
        if not (20 <= self.pulse <= 250):
            raise ValueError(
                f"Pulse must be between 20 and 250 bpm. Got: {self.pulse}"
            )
        invalid = [s for s in self.symptoms if s not in VALID_SYMPTOMS]
        if invalid:
            raise ValueError(
                f"Unknown symptom(s): {invalid}. "
                f"Valid options: {sorted(VALID_SYMPTOMS)}"
            )


@dataclass
class TriageResult:
    """The outcome of assessing a patient."""

    patient_name: str
    category: str
    score: int
    reasons: List[str] = field(default_factory=list)

    def __str__(self):
        lines = [
            f"Patient : {self.patient_name}",
            f"Category: {self.category}",
            f"Score   : {self.score}",
            "Reasons :",
        ]
        for reason in self.reasons:
            lines.append(f"  • {reason}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scoring rules
# ---------------------------------------------------------------------------

def _score_symptoms(symptoms: List[str]) -> tuple[int, List[str]]:
    """Return (points, reasons) based on reported symptoms."""
    critical = {
        "unconscious": (40, "Patient is unconscious"),
        "severe_bleeding": (35, "Severe bleeding reported"),
        "stroke_signs": (40, "Stroke signs present"),
        "chest_pain": (30, "Chest pain reported"),
        "difficulty_breathing": (30, "Difficulty breathing reported"),
    }
    serious = {
        "high_fever": (15, "High fever symptom reported"),
        "vomiting": (10, "Vomiting reported"),
        "dizziness": (10, "Dizziness reported"),
        "moderate_pain": (10, "Moderate pain reported"),
    }
    minor = {
        "minor_cut": (2, "Minor cut reported"),
        "mild_headache": (2, "Mild headache reported"),
        "none": (0, None),
    }

    score = 0
    reasons: List[str] = []

    for symptom in symptoms:
        for mapping in (critical, serious, minor):
            if symptom in mapping:
                pts, msg = mapping[symptom]
                score += pts
                if msg:
                    reasons.append(msg)

    return score, reasons


def _score_vitals(patient: Patient) -> tuple[int, List[str]]:
    """Return (points, reasons) based on vital signs."""
    score = 0
    reasons: List[str] = []

    # Pain level
    if patient.pain_level >= 8:
        score += 20
        reasons.append(f"Severe pain (level {patient.pain_level}/10)")
    elif patient.pain_level >= 5:
        score += 10
        reasons.append(f"Moderate pain (level {patient.pain_level}/10)")
    elif patient.pain_level >= 3:
        score += 4
        reasons.append(f"Mild pain (level {patient.pain_level}/10)")

    # Fever
    if patient.fever >= 40.0:
        score += 20
        reasons.append(f"Very high fever ({patient.fever} °C)")
    elif patient.fever >= 38.5:
        score += 10
        reasons.append(f"High fever ({patient.fever} °C)")
    elif patient.fever >= 37.5:
        score += 4
        reasons.append(f"Low-grade fever ({patient.fever} °C)")

    # Pulse
    if patient.pulse > 140 or patient.pulse < 40:
        score += 20
        reasons.append(f"Dangerous pulse rate ({patient.pulse} bpm)")
    elif patient.pulse > 110 or patient.pulse < 55:
        score += 10
        reasons.append(f"Abnormal pulse rate ({patient.pulse} bpm)")

    # Shortness of breath
    if patient.shortness_of_breath:
        score += 25
        reasons.append("Shortness of breath present")

    # Age risk factor
    if patient.age < 2 or patient.age > 75:
        score += 10
        reasons.append(f"High-risk age group ({patient.age} years)")
    elif patient.age < 12 or patient.age > 60:
        score += 4
        reasons.append(f"Elevated-risk age group ({patient.age} years)")

    return score, reasons


# ---------------------------------------------------------------------------
# Main triage function
# ---------------------------------------------------------------------------

def assess_patient(patient: Patient) -> TriageResult:
    """
    Evaluate a patient and return a TriageResult with a category.

    The total score is the sum of symptom and vital-sign subscores:
        >= 35  → IMMEDIATE
        >= 20  → URGENT
        >= 8   → NORMAL
        < 8    → NON-URGENT
    """
    sym_score, sym_reasons = _score_symptoms(patient.symptoms)
    vital_score, vital_reasons = _score_vitals(patient)

    total_score = sym_score + vital_score
    all_reasons = sym_reasons + vital_reasons

    if total_score >= 35:
        category = "IMMEDIATE"
    elif total_score >= 20:
        category = "URGENT"
    elif total_score >= 8:
        category = "NORMAL"
    else:
        category = "NON-URGENT"

    return TriageResult(
        patient_name=patient.name,
        category=category,
        score=total_score,
        reasons=all_reasons,
    )


def prioritise_patients(patients: List[Patient]) -> List[TriageResult]:
    """
    Assess a list of patients and return results sorted by priority
    (IMMEDIATE first, NON-URGENT last).
    """
    results = [assess_patient(p) for p in patients]
    results.sort(key=lambda r: TRIAGE_LEVELS.index(r.category))
    return results
