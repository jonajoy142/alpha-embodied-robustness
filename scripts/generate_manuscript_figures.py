#!/usr/bin/env python3
"""
Generate publication-quality manuscript figures for the Alpha research paper.
Outputs figures into figures/ and artifacts/final_150_matrix/figures/.
"""

from __future__ import annotations

import os
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

# Styling configuration
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 13,
    "lines.linewidth": 1.75,
    "lines.markersize": 6,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
})

OUT_DIRS = [
    Path("figures"),
    Path("artifacts/final_150_matrix/figures"),
    Path("artifacts/figures"),
]

for d in OUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)


def save_figure(fig: plt.Figure, basename: str) -> None:
    for d in OUT_DIRS:
        dest = d / basename
        fig.savefig(dest, dpi=300, bbox_inches="tight")
    print(f"Saved figure: {basename}")
    plt.close(fig)


# ==============================================================================
# Figure 1: Architecture Diagram
# ==============================================================================
# ==============================================================================
# Figure 1: Architecture Diagram (Professional 4-Panel Modular Layout)
# ==============================================================================
def make_fig1_architecture() -> None:
    fig, ax = plt.subplots(figsize=(15.0, 8.0), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    # -------------------------------------------------------------------------
    # Color Palette (Publication Grade - Clean, High Contrast, Accessible)
    # -------------------------------------------------------------------------
    C_BG_PANEL = "#f8fafc"       # Slate 50
    C_BORDER_PANEL = "#94a3b8"   # Slate 400
    
    C_BOX_BG = "#ffffff"         # Pure white
    C_BOX_BORDER = "#1e293b"     # Slate 800
    C_BOX_TITLE = "#0f172a"      # Slate 900
    C_BOX_SUB = "#475569"        # Slate 600

    C_FAULT_BG = "#fff7ed"       # Orange 50
    C_FAULT_BORDER = "#ea580c"   # Orange 600
    C_FAULT_TITLE = "#9a3412"    # Orange 800
    C_FAULT_SUB = "#c2410c"      # Orange 700

    C_SAFETY_BG = "#f0fdf4"      # Emerald 50
    C_SAFETY_BORDER = "#059669"  # Emerald 600
    C_SAFETY_TITLE = "#064e3b"   # Emerald 900
    C_SAFETY_SUB = "#047857"     # Emerald 700

    C_REJECT_BG = "#fef2f2"      # Red 50
    C_REJECT_BORDER = "#dc2626"  # Red 600
    C_REJECT_TITLE = "#991b1b"   # Red 800
    C_REJECT_SUB = "#b91c1c"     # Red 700

    C_ORACLE_BG = "#eff6ff"      # Blue 50
    C_ORACLE_BORDER = "#2563eb"  # Blue 600
    C_ORACLE_TITLE = "#1e40af"   # Blue 800
    C_ORACLE_SUB = "#1d4ed8"     # Blue 700

    # -------------------------------------------------------------------------
    # Drawing Primitives
    # -------------------------------------------------------------------------
    def draw_container(x, y, w, h, title="", bg=C_BG_PANEL, border=C_BORDER_PANEL):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.0,rounding_size=1.2",
            facecolor=bg, edgecolor=border, lw=1.2, ls="--", zorder=1
        )
        ax.add_patch(rect)
        if title:
            ax.text(x + 1.2, y + h - 2.8, title, ha="left", va="center",
                    fontsize=7.8, fontweight="bold", color="#334155", zorder=2)

    def draw_component(x_c, y_c, w, h, title, sub="", bg=C_BOX_BG, border=C_BOX_BORDER,
                       t_col=C_BOX_TITLE, s_col=C_BOX_SUB, zorder=3):
        rect = patches.FancyBboxPatch(
            (x_c - w/2, y_c - h/2), w, h,
            boxstyle="round,pad=0.0,rounding_size=0.8",
            facecolor=bg, edgecolor=border, lw=1.4, zorder=zorder
        )
        ax.add_patch(rect)
        if sub:
            ax.text(x_c, y_c + h*0.17, title, ha="center", va="center",
                    fontsize=9.0, fontweight="bold", color=t_col, zorder=zorder+1)
            ax.text(x_c, y_c - h*0.20, sub, ha="center", va="center",
                    fontsize=7.4, color=s_col, zorder=zorder+1)
        else:
            ax.text(x_c, y_c, title, ha="center", va="center",
                    fontsize=9.0, fontweight="bold", color=t_col, zorder=zorder+1)

    def draw_fault_box(x_c, y_c, w, h, title, sub=""):
        rect = patches.FancyBboxPatch(
            (x_c - w/2, y_c - h/2), w, h,
            boxstyle="round,pad=0.0,rounding_size=0.8",
            facecolor=C_FAULT_BG, edgecolor=C_FAULT_BORDER, lw=1.5, zorder=4
        )
        ax.add_patch(rect)
        if sub:
            ax.text(x_c, y_c + h*0.17, title, ha="center", va="center",
                    fontsize=8.6, fontweight="bold", color=C_FAULT_TITLE, zorder=5)
            ax.text(x_c, y_c - h*0.20, sub, ha="center", va="center",
                    fontsize=7.2, color=C_FAULT_SUB, zorder=5)
        else:
            ax.text(x_c, y_c, title, ha="center", va="center",
                    fontsize=8.6, fontweight="bold", color=C_FAULT_TITLE, zorder=5)

    # -------------------------------------------------------------------------
    # 1. Containers with Dedicated Inter-Stage Routing Channels
    # -------------------------------------------------------------------------
    # Stage 1: x in [1.8, 21.8] (w=20.0)
    draw_container(1.8, 18.0, 20.0, 76.0, "1. PERCEPTION & SIMULATION")

    # Channel 1: x in [21.8, 24.5] (w=2.7) -> Bus at x=23.0

    # Stage 2: x in [24.5, 71.5] (w=47.0)
    draw_container(24.5, 54.5, 47.0, 39.5, "2A. LLM PLANNER PIPELINE (ARM A)")
    draw_container(24.5, 18.0, 47.0, 33.5, "2B. SCRIPTED ORACLE PIPELINE (ARM B)")

    # Channel 2: x in [71.5, 77.5] (w=6.0) -> Conduit at x=74.75

    # Stage 3: x in [77.5, 98.2] (w=20.7)
    draw_container(77.5, 18.0, 20.7, 76.0, "3. CONTROL & ACTUATION (BODY)")

    # Foundation: PyBullet Safety Monitor (full width)
    rect_safety = patches.FancyBboxPatch(
        (2.0, 3.0), 96.0, 13.0,
        boxstyle="round,pad=0.0,rounding_size=1.0",
        facecolor=C_SAFETY_BG, edgecolor=C_SAFETY_BORDER, lw=1.5, zorder=3
    )
    ax.add_patch(rect_safety)
    ax.text(50.0, 11.2, "Synchronous PyBullet Safety Monitor (240 Hz) & Telemetry Logging",
            ha="center", va="center", fontsize=9.8, fontweight="bold", color=C_SAFETY_TITLE, zorder=4)
    ax.text(50.0, 7.3, "Collision Force Threshold: F_thresh = 3000 N on Links 0-6 (excludes table base & active grasp reaction)\n"
                       "Temporal Deduplication Window: 15 simulation steps (~0.0625s) | Workspace Enclosure: [0.15, 0.95] x [-0.45, 0.55] x [0.55, 1.25] m",
            ha="center", va="center", fontsize=7.6, color=C_SAFETY_SUB, zorder=4)

    # -------------------------------------------------------------------------
    # 2. Stage 1 Components (Perception & Simulation)
    # -------------------------------------------------------------------------
    draw_component(11.75, 78.0, 16.5, 8.5, "PyBullet DIRECT", "Franka 7-DOF Manipulation Scene")
    draw_component(11.75, 56.0, 16.5, 8.5, "Observation Hook", "wrap_observation() Capture")
    draw_fault_box(11.75, 31.0, 16.5, 9.5, "[F1] Sensor Lag Injection",
                   "Ring Buffer Delay: Tau_lag = 0.500s\nMax Staleness Delta_pos <= 2.50cm")

    # -------------------------------------------------------------------------
    # 3. Stage 2A Components (LLM Planner Pipeline)
    # -------------------------------------------------------------------------
    draw_fault_box(48.0, 84.5, 18.0, 6.5, "[F4] Output Corruption",
                   "Key Deletion / JSON Syntax Truncation")

    draw_component(32.0, 71.5, 13.0, 9.0, "LLM Planner", "Ollama: llama3 (T=0.0)\nPrompt -> JSON Plan")
    draw_component(48.0, 71.5, 14.0, 9.0, "Output Interceptor", "intercept_output()\nRaw Text Stream Capture")
    draw_component(64.0, 71.5, 13.5, 9.0, "Pydantic Validator", "validate_raw_plan()\nStrict Schema Enforcement")

    draw_component(64.0, 59.0, 13.5, 5.5, "Schema Rejection", "actions=[] -> Fail-Stop",
                   bg=C_REJECT_BG, border=C_REJECT_BORDER, t_col=C_REJECT_TITLE, s_col=C_REJECT_SUB)

    # -------------------------------------------------------------------------
    # 4. Stage 2B Components (Scripted Oracle Pipeline)
    # -------------------------------------------------------------------------
    draw_component(33.5, 34.0, 15.5, 9.0, "Scripted Oracle", "Deterministic Kinematics\nLinear Kinematic Waypoints")
    draw_component(57.0, 34.0, 24.0, 9.0, "In-Memory Action Objects",
                   "Native Compiled Dataclasses: MOVE, GRIP, REL\nBypasses Serialization & Schema Validation Entirely",
                   bg=C_ORACLE_BG, border=C_ORACLE_BORDER, t_col=C_ORACLE_TITLE, s_col=C_ORACLE_SUB)

    # -------------------------------------------------------------------------
    # 5. Stage 3 Components (Control & Actuation - Body)
    # -------------------------------------------------------------------------
    draw_fault_box(88.0, 84.5, 17.5, 6.5, "[F3] Reach Fault",
                   "Radial Goal Offset (Delta z = 0.55m)")
    draw_component(88.0, 69.5, 17.5, 10.0, "ControlService (IK)",
                   "Cartesian Trajectory Generator\nDamped Least-Squares (DLS) IK")
    draw_component(88.0, 43.5, 17.5, 9.5, "PyBullet Actuation",
                   "Franka Parallel-Jaw Gripper\nRigid-Body Contact Constraints")
    draw_fault_box(88.0, 26.5, 17.5, 7.0, "[F2] Grip Slip",
                   "Single-Lift Latch Release\nConstraint Force Degradation")

    # -------------------------------------------------------------------------
    # 6. Clean Orthogonal Dataflow Arrows (No Crossings, Guaranteed Clearances)
    # -------------------------------------------------------------------------
    arr_solid = dict(arrowstyle="-|>", lw=1.6, color="#0f172a", mutation_scale=11)
    arr_dashed = dict(arrowstyle="-|>", lw=1.5, color="#ea580c", ls="--", mutation_scale=10)
    arr_valid = dict(arrowstyle="-|>", lw=1.6, color="#16a34a", mutation_scale=11)
    arr_oracle = dict(arrowstyle="-|>", lw=1.6, color="#2563eb", ls="-.", mutation_scale=11)
    arr_red = dict(arrowstyle="-|>", lw=1.5, color="#dc2626", mutation_scale=10)

    # (A) PyBullet Simulation -> Observation Hook
    ax.annotate("", xy=(11.75, 60.5), xytext=(11.75, 73.5), arrowprops=arr_solid)

    # (B) [F1] Sensor Lag -> Observation Hook
    ax.annotate("", xy=(11.75, 51.5), xytext=(11.75, 36.0), arrowprops=arr_dashed)
    ax.text(11.75, 43.8, "Stale Buffer", ha="center", va="center", fontsize=7.2,
            fontweight="bold", color="#c2410c",
            bbox=dict(boxstyle="round,pad=0.2", fc="#fff7ed", ec="#fed7aa", lw=0.6))

    # (C) Observation Hook -> Dual-Arm Split Bus (in Channel 1 at x=23.0)
    ax.plot([20.0, 23.0], [56.0, 56.0], color="#0f172a", lw=1.6, zorder=2)
    # Up to LLM Planner at y=71.5
    ax.plot([23.0, 23.0, 25.5], [56.0, 71.5, 71.5], color="#0f172a", lw=1.6, zorder=2)
    ax.annotate("", xy=(25.5, 71.5), xytext=(24.2, 71.5), arrowprops=arr_solid)
    # Down to Scripted Oracle at y=34.0
    ax.plot([23.0, 23.0, 25.75], [56.0, 34.0, 34.0], color="#0f172a", lw=1.6, zorder=2)
    ax.annotate("", xy=(25.75, 34.0), xytext=(24.5, 34.0), arrowprops=arr_solid)

    # (D) Stage 2A Linear Flow (along y = 71.5)
    ax.annotate("", xy=(41.0, 71.5), xytext=(38.5, 71.5), arrowprops=arr_solid)
    ax.annotate("", xy=(57.25, 71.5), xytext=(55.0, 71.5), arrowprops=arr_solid)

    # (E) [F4] Corruption -> Output Interceptor
    ax.annotate("", xy=(48.0, 76.2), xytext=(48.0, 81.2), arrowprops=arr_dashed)

    # (F) Pydantic Validator Branches
    # Invalid Schema -> Schema Rejection (downwards)
    ax.annotate("", xy=(64.0, 62.0), xytext=(64.0, 67.0), arrowprops=arr_red)
    ax.text(64.0, 64.5, "Schema Error", ha="center", va="center", fontsize=6.8,
            fontweight="bold", color="#dc2626",
            bbox=dict(boxstyle="round,pad=0.15", fc="#fef2f2", ec="#fca5a5", lw=0.5))

    # Valid Schema -> ControlService (crosses Channel 2 at y=71.5)
    ax.plot([70.75, 79.25], [71.5, 71.5], color="#16a34a", lw=1.6, zorder=3)
    ax.annotate("", xy=(79.25, 71.5), xytext=(77.5, 71.5), arrowprops=arr_valid)
    ax.text(74.75, 74.0, "Valid Plan", ha="center", va="center", fontsize=7.4,
            fontweight="bold", color="#16a34a",
            bbox=dict(boxstyle="round,pad=0.2", fc="#ffffff", ec="#16a34a", lw=0.8, zorder=6))

    # (G) Stage 2B Scripted Oracle Flow
    ax.annotate("", xy=(45.0, 34.0), xytext=(41.25, 34.0), arrowprops=arr_solid)

    # In-Memory Objects -> ControlService (crosses into Channel 2 at x=74.75, routes up to y=66.5)
    ax.plot([69.0, 74.75, 74.75, 79.25], [34.0, 34.0, 66.5, 66.5],
            color="#2563eb", lw=1.6, ls="-.", zorder=3)
    ax.annotate("", xy=(79.25, 66.5), xytext=(77.5, 66.5), arrowprops=arr_oracle)
    ax.text(74.75, 47.0, "Oracle Direct\nExecution", ha="center", va="center", fontsize=7.2,
            fontweight="bold", color="#2563eb",
            bbox=dict(boxstyle="round,pad=0.25", fc="#ffffff", ec="#2563eb", lw=0.8, zorder=6))

    # (H) Stage 3 Control & Actuation Flow
    # [F3] Reach Fault -> ControlService
    ax.annotate("", xy=(88.0, 74.8), xytext=(88.0, 81.0), arrowprops=arr_dashed)

    # ControlService -> PyBullet Actuation
    ax.annotate("", xy=(88.0, 48.5), xytext=(88.0, 64.2), arrowprops=arr_solid)
    ax.text(88.0, 56.5, "Trajectory q(t)\nJoint Commands", ha="center", va="center", fontsize=7.0,
            fontweight="bold", color="#334155",
            bbox=dict(boxstyle="round,pad=0.2", fc="#f8fafc", ec="#cbd5e1", lw=0.5))

    # [F2] Grip Slip -> PyBullet Actuation
    ax.annotate("", xy=(88.0, 38.5), xytext=(88.0, 30.2), arrowprops=arr_dashed)

    # -------------------------------------------------------------------------
    # Main Figure Title
    # -------------------------------------------------------------------------
    ax.text(50.0, 97.2, "Figure 1: Alpha Fault-Injection Architecture & Component Operational Boundaries",
            ha="center", va="center", fontsize=12.2, fontweight="bold", color="#0f172a")

    save_figure(fig, "fig1_architecture.png")


# ==============================================================================
# Figure 2: Success Rates by Fault and Planner (Final 150 Matrix)
# ==============================================================================
def make_fig2_success_rates() -> None:
    categories = ["Control", "F1: Lag", "F2: Slip", "F3: Reach", "F4: Corruption", "Concurrent"]
    oracle_scores = [100.0, 100.0, 40.0, 0.0, 100.0, 40.0]
    llm_scores = [100.0, 100.0, 40.0, 0.0, 0.0, 40.0]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    r1 = ax.bar(x - width/2, oracle_scores, width, label="Scripted Oracle (N=75)", color="#1f77b4", edgecolor="#0d3b66")
    r2 = ax.bar(x + width/2, llm_scores, width, label="LLM: llama3:latest (N=75)", color="#e07a5f", edgecolor="#8d321b")

    ax.set_ylabel("Task Success Rate (%)")
    ax.set_title("150-Episode Matrix: Scripted Oracle vs. LLM Agent Performance", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 115)
    ax.grid(axis="y")
    ax.legend(loc="upper right", frameon=True)

    for rects in [r1, r2]:
        for b in rects:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width()/2., h + 2, f"{int(h)}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Annotation highlighting 0 discordant pairs on physical faults
    ax.annotate("0 discordant pairs\n(identical 55% physical success)",
                xy=(1, 102), xytext=(1.2, 80),
                arrowprops=dict(facecolor="black", arrowstyle="->", lw=1.2),
                fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#fff3cd", ec="#ffeeba"))

    ax.annotate("Discrepancy driven\nentirely by F4 validation",
                xy=(4, 50), xytext=(3.3, 70),
                arrowprops=dict(facecolor="black", arrowstyle="->", lw=1.2),
                fontsize=8.5, bbox=dict(boxstyle="round,pad=0.3", fc="#d4edda", ec="#c3e6cb"))

    save_figure(fig, "fig2_matrix_success_rates.png")


# ==============================================================================
# Figure 3: F2 Slip Intensity vs Realized Slip & Success
# ==============================================================================
def make_fig3_f2_slip() -> None:
    intensities = [0.33, 0.66, 1.00]
    labels = ["Low (0.33)", "Medium (0.66)", "High (1.00)"]
    calibrated_prob = [0.270, 0.525, 0.865]
    realized_slip = [0.40, 0.60, 0.80]
    success_rate = [0.60, 0.40, 0.20]

    fig, ax1 = plt.subplots(figsize=(7, 4.2))

    x = np.arange(len(labels))
    w = 0.28

    b1 = ax1.bar(x - w/2, [p * 100 for p in realized_slip], w, label="Realized Slip Rate (%)", color="#d9534f", edgecolor="#a52a2a")
    b2 = ax1.bar(x + w/2, [s * 100 for s in success_rate], w, label="Task Success Rate (%)", color="#5cb85c", edgecolor="#398439")

    # Calibrated requested probability curve
    ax1.plot(x, [p * 100 for p in calibrated_prob], marker="o", color="#0275d8", ls="--", lw=2, label="Calibrated P(Slip) (%)")

    ax1.set_ylabel("Rate (%)")
    ax1.set_xlabel("Fault Intensity Label (Parameter)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0, 105)
    ax1.grid(axis="y")
    ax1.set_title("F2 Grip Slip: Actuator Degradation and Matched Success Decay", pad=12)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=True)

    for b in b1 + b2:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width()/2., h + 2, f"{int(h)}%", ha="center", va="bottom", fontsize=8.5)

    save_figure(fig, "fig4_f2_slip_degradation.png")
    # Backwards-compatible alias
    for d in OUT_DIRS:
        import shutil
        shutil.copy(d / "fig4_f2_slip_degradation.png", d / "fig3_f2_slip_degradation.png")


# ==============================================================================
# Figure 4 / 5: F3 Continuous Placement Error
# ==============================================================================
def make_fig4_f3_placement_error() -> None:
    intensities = [0.00, 0.33, 0.66, 1.00]
    labels = ["Control", "Low", "Medium", "High"]
    
    oracle_dist = [0.0349, 0.1794, 0.2248, 0.2830]
    llm_dist = [0.0349, 0.1839, 0.3176, 0.2693]

    fig, ax = plt.subplots(figsize=(7.5, 4.4))

    ax.plot(labels, oracle_dist, marker="s", color="#1f77b4", lw=2, label="Scripted Oracle (Monotonic)")
    ax.plot(labels, llm_dist, marker="o", color="#e07a5f", lw=2, label="LLM: llama3:latest (Non-Monotonic)")

    # Success threshold
    ax.axhline(0.05, color="red", ls=":", lw=1.8, label="Success Radius Threshold (0.05 m)")
    ax.axhline(0.0349, color="gray", ls="--", lw=1.2, label="Control Baseline Center (0.035 m)")

    ax.set_ylabel("Final Distance to Target Center (m)")
    ax.set_xlabel("Kinematic Reach Offset Intensity")
    ax.set_title("F3 Unreachable IK: Continuous Placement Error vs. Injected Offset", pad=12)
    ax.set_ylim(0, 0.38)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True)

    # Point annotations
    for i, (od, ld) in enumerate(zip(oracle_dist, llm_dist)):
        if i > 0:
            ax.text(i - 0.05, od - 0.022, f"{od:.3f}m", ha="right", fontsize=8, color="#1f77b4")
            ax.text(i + 0.05, ld + 0.015, f"{ld:.3f}m", ha="left", fontsize=8, color="#e07a5f")

    save_figure(fig, "fig5_f3_placement_error.png")
    for d in OUT_DIRS:
        import shutil
        shutil.copy(d / "fig5_f3_placement_error.png", d / "fig4_f3_placement_error.png")


# ==============================================================================
# Figure 3 / 5: F1 Sensor Lag Saturation
# ==============================================================================
def make_fig5_f1_staleness() -> None:
    labels = ["Low (0.33)", "Medium (0.66)", "High (1.00)"]
    requested = [0.562, 1.024, 1.500]
    observed = [0.500, 0.500, 0.500]
    divergence = [0.025, 0.025, 0.025] # meters

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.0))

    # Left: Temporal lag
    x = np.arange(len(labels))
    w = 0.35
    ax1.bar(x - w/2, requested, w, label="Requested Lag", color="#90caf9", edgecolor="#1565c0")
    ax1.bar(x + w/2, observed, w, label="Observed/Applied Lag", color="#1565c0", edgecolor="#0d47a1")
    ax1.axhline(0.500, color="darkred", ls="--", label="Buffer Capacity Limit (0.500s)")
    ax1.set_ylabel("Lag Duration (seconds)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_ylim(0, 1.8)
    ax1.grid(axis="y")
    ax1.set_title("(a) Temporal Sensor Lag Saturation")
    ax1.legend(loc="upper left", fontsize=8.5)

    # Right: Spatial divergence vs tolerance
    ax2.bar(x, [d * 100 for d in divergence], width=0.4, color="#ffb74d", edgecolor="#e65100", label="Block Staleness Divergence")
    ax2.axhline(8.0, color="green", ls="--", lw=2, label="Gripper Jaw Opening Tolerance (8.0 cm)")
    ax2.set_ylabel("Displacement / Clearance (cm)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_ylim(0, 10.5)
    ax2.grid(axis="y")
    ax2.set_title("(b) Spatial Staleness vs. Grasp Envelope")
    ax2.legend(loc="upper left", fontsize=8.5)

    plt.tight_layout()
    save_figure(fig, "fig3_f1_staleness_saturation.png")
    for d in OUT_DIRS:
        import shutil
        shutil.copy(d / "fig3_f1_staleness_saturation.png", d / "fig5_f1_staleness_saturation.png")


# ==============================================================================
# Figure 6: F4 Serialization & Schema Execution Path
# ==============================================================================
# ==============================================================================
# Figure 6: F4 Serialization & Schema Execution Path (Spacious Layout)
# ==============================================================================
def make_fig6_f4_path() -> None:
    fig, ax = plt.subplots(figsize=(12, 5.0), dpi=300)
    ax.axis("off")
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)

    def draw_path_box(x_c, y_c, w, h, title, subtitle="", bg="#f8fafc", border="#334155", title_color="#0f172a"):
        rect = patches.FancyBboxPatch((x_c - w/2, y_c - h/2), w, h, boxstyle="round,pad=0.3,rounding_size=0.8",
                                      facecolor=bg, edgecolor=border, lw=1.4, zorder=2)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x_c, y_c + h*0.18, title, ha="center", va="center", fontsize=9, fontweight="bold",
                    color=title_color, zorder=3)
            ax.text(x_c, y_c - h*0.22, subtitle, ha="center", va="center", fontsize=7.8, color="#475569",
                    zorder=3)
        else:
            ax.text(x_c, y_c, title, ha="center", va="center", fontsize=9, fontweight="bold",
                    color=title_color, zorder=3)

    # Upper branch: LLM Pipeline (y=72)
    draw_path_box(10, 72, 14, 15, "LLM Agent", "Ollama llama3:latest")
    draw_path_box(30, 72, 16, 15, "Raw JSON Output", "Text Plan Stream")
    draw_path_box(52, 72, 18, 15, "F4 Interceptor", "Key Deletion / Corruption",
                  bg="#fff7ed", border="#ea580c", title_color="#c2410c")
    draw_path_box(74, 72, 17, 15, "Pydantic Validator", "ValidationError Trapped",
                  bg="#f8fafc", border="#475569", title_color="#0f172a")
    draw_path_box(92, 72, 13, 15, "0% Success", "Clean Fail-Stop\n(actions=[])",
                  bg="#fef2f2", border="#ef4444", title_color="#b91c1c")

    # Lower branch: Scripted Oracle Pipeline (y=28)
    draw_path_box(10, 28, 14, 15, "Scripted Oracle", "Deterministic Controller")
    draw_path_box(36, 28, 25, 15, "In-Memory Python Objects", "Compiled Action Dataclasses")
    draw_path_box(68, 28, 26, 15, "Bypasses Serialization Layer", "No JSON / Schema Parsing Involved",
                  bg="#eff6ff", border="#3b82f6", title_color="#1d4ed8")
    draw_path_box(92, 28, 13, 15, "100% Success", "Goal Completed\n(Clean Reaches)",
                  bg="#f0fdf4", border="#16a34a", title_color="#15803d")

    arr = dict(arrowstyle="->", lw=1.6, color="#334155")
    # Upper branch arrows
    ax.annotate("", xy=(21, 72), xytext=(17.5, 72), arrowprops=arr)
    ax.annotate("", xy=(42, 72), xytext=(38.5, 72), arrowprops=arr)
    ax.annotate("", xy=(64.5, 72), xytext=(61.5, 72), arrowprops=arr)
    ax.annotate("", xy=(84.5, 72), xytext=(83, 72), arrowprops=arr)

    # Lower branch arrows
    ax.annotate("", xy=(22.5, 28), xytext=(17.5, 28), arrowprops=arr)
    ax.annotate("", xy=(54, 28), xytext=(49, 28), arrowprops=arr)
    ax.annotate("", xy=(84.5, 28), xytext=(81.5, 28), arrowprops=arr)

    ax.set_title("Figure 6: Execution Path Divergence Under F4 (Planner Output Corruption)",
                 fontsize=11.5, fontweight="bold", pad=15)
    save_figure(fig, "fig6_f4_serialization_path.png")


# ==============================================================================
# Figure 7: Historical 169-Attempt Audit
# ==============================================================================
def make_fig7_pilot_audit() -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))

    cohorts = ["OpenAI gpt-4o (Discarded)", "Ollama llama3:latest (Accepted)"]
    crashes = [99, 0]
    task_failures = [0, 50]
    successes = [0, 20]

    b1 = ax.bar(cohorts, crashes, label="Infrastructure Failures (HTTP 429 / Runtime)", color="#d9534f", edgecolor="#a52a2a", width=0.45)
    b2 = ax.bar(cohorts, task_failures, bottom=crashes, label="Task Execution Failures", color="#f0ad4e", edgecolor="#d58512", width=0.45)
    b3 = ax.bar(cohorts, successes, bottom=[i+j for i, j in zip(crashes, task_failures)], label="Completed Task Successes", color="#5cb85c", edgecolor="#398439", width=0.45)

    ax.set_ylabel("Total Attempt Invocations")
    ax.set_title("Audit of 169 Historical Pilot Attempts: Discard Bias Transparency", pad=12)
    ax.set_ylim(0, 115)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(axis="y")

    # Value labels
    ax.text(0, 45, "99 Aborts\n(100%)", ha="center", va="center", color="white", fontweight="bold", fontsize=10)
    ax.text(1, 25, "50 Failures", ha="center", va="center", color="white", fontweight="bold", fontsize=9.5)
    ax.text(1, 60, "20 Successes\n(28.6%)", ha="center", va="center", color="white", fontweight="bold", fontsize=9.5)

    save_figure(fig, "fig7_pilot_accounting.png")


if __name__ == "__main__":
    make_fig1_architecture()
    make_fig2_success_rates()
    make_fig3_f2_slip()
    make_fig4_f3_placement_error()
    make_fig5_f1_staleness()
    make_fig6_f4_path()
    make_fig7_pilot_audit()
    print("\nAll manuscript figures successfully generated.")
