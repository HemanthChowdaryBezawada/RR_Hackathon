from pathlib import Path
import re
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data_pack"
FILES = [
    "ball_by_ball.csv",
    "matches.csv",
    "playing_eleven.csv",
    "teams.csv",
    "competitions.csv",
    "competition_team_player_mapping.csv",
]
MAX_VALUES = 25


def md(value: Any, limit: int | None = None) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("|", r"\|").replace("\n", " ")
    if limit is not None and len(text) > limit:
        text = text[: max(0, limit - 3)] + "..."
    return text


def pct(count: int, total: int) -> str:
    return f"{(100 * count / total):.2f}%" if total else "0.00%"


def is_id_column(name: str) -> bool:
    return "id" in name.lower()


def is_date_column(name: str, series: pd.Series) -> bool:
    lowered = name.lower()
    if any(token in lowered for token in ("date", "datetime", "timestamp", "season")):
        return True
    return pd.api.types.is_datetime64_any_dtype(series)


def example_values(series: pd.Series) -> str:
    values = series.dropna().head(3).tolist()
    return ", ".join(md(value, 40) for value in values)


def format_stats(series: pd.Series) -> list[str]:
    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if not numeric.empty:
            return [f"min={md(numeric.min())}", f"max={md(numeric.max())}",
                    f"mean={numeric.mean():.4g}"]
    return []


def format_date_stats(series: pd.Series) -> list[str]:
    parsed = pd.to_datetime(series, errors="coerce")
    parsed = parsed.dropna()
    if not parsed.empty:
        return [f"min={parsed.min().date()}", f"max={parsed.max().date()}"]
    return []


def table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |",
             "| " + " | ".join("---" for _ in headers) + " |"]
    lines.extend("| " + " | ".join(md(cell) for cell in row) + " |" for row in rows)
    return lines


def values_for(series: pd.Series) -> list[tuple[str, int]]:
    counts = series.dropna().value_counts(dropna=False)
    return [(md(value, 80), int(count)) for value, count in counts.items()]


def find_column(df: pd.DataFrame, terms: tuple[str, ...]) -> str | None:
    for column in df.columns:
        lowered = str(column).lower()
        if any(term in lowered for term in terms):
            return str(column)
    return None


def find_exact_column(df: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    lowered = {str(column).lower(): str(column) for column in df.columns}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def id_values(df: pd.DataFrame, column: str) -> set[str]:
    return set(df[column].dropna().map(str))


def main() -> None:
    report: list[str] = [
        "# CSV Schema Inspection Report",
        "",
        "Inspection only: files were read with pandas and not cleaned, transformed, or modeled.",
        "",
    ]
    frames: dict[str, pd.DataFrame] = {}
    missing: list[str] = []

    for filename in FILES:
        path = DATA_DIR / filename
        if not path.exists():
            missing.append(filename)
            report += [f"## {filename}", "", "**Missing file.**", ""]
            continue
        try:
            frame = pd.read_csv(path, low_memory=False)
            frames[filename] = frame
        except Exception as exc:
            report += [f"## {filename}", "", f"**Could not read file:** `{md(exc)}`", ""]
            continue

        report += [
            f"## {filename}", "",
            f"- Path: `{path.relative_to(ROOT)}`",
            f"- File size: {path.stat().st_size / (1024 * 1024):.3f} MB",
            f"- Rows: {len(frame):,}",
            f"- Columns: {len(frame.columns):,}", "",
            "### Columns", "",
        ]
        column_rows = []
        for column in frame.columns:
            series = frame[column]
            nulls = int(series.isna().sum())
            column_rows.append([
                str(column), str(series.dtype), nulls, pct(nulls, len(frame)),
                int(series.nunique(dropna=True)), example_values(series),
            ])
        report += table(
            ["Column", "Dtype", "Null count", "Null %", "Unique", "3 examples"],
            column_rows,
        ) + ["", "### First 5 rows", ""]
        preview = frame.head(5).copy()
        preview = preview.map(lambda value: md(value, 40))
        report += table([str(column) for column in preview.columns],
                        preview.values.tolist()) + ["", "### Numeric and date-like summaries", ""]
        summary_rows = []
        for column in frame.columns:
            stats = format_stats(frame[column])
            date_stats = format_date_stats(frame[column]) if is_date_column(str(column), frame[column]) else []
            if stats or date_stats:
                summary_rows.append([str(column), "; ".join(stats + date_stats)])
        report += table(["Column", "Summary"], summary_rows) if summary_rows else ["No numeric or date-like columns detected."]
        report += ["", "### Low-cardinality value counts", ""]
        low_cardinality = []
        for column in frame.columns:
            unique = int(frame[column].nunique(dropna=True))
            if unique <= MAX_VALUES:
                counts = "; ".join(f"{value} ({count})" for value, count in values_for(frame[column]))
                if frame[column].isna().any():
                    counts += f"; <NA> ({int(frame[column].isna().sum())})"
                low_cardinality.append([str(column), counts or "(no values)"])
        report += table(["Column", "Value counts"], low_cardinality) if low_cardinality else ["None."]
        report += ["", "### Candidate key check", ""]
        key_rows = []
        for column in frame.columns:
            if is_id_column(str(column)):
                non_null = frame[column].dropna()
                key_rows.append([str(column), "yes" if non_null.is_unique else "no",
                                 f"{len(non_null):,} non-null values"])
        report += table(["Column", "Unique among non-null values", "Basis"], key_rows) if key_rows else ["No columns containing `id`."]
        report.append("")

    report += ["# CROSS-FILE CHECKS", ""]
    column_files: dict[str, list[str]] = {}
    for filename, frame in frames.items():
        for column in frame.columns:
            column_files.setdefault(str(column), []).append(filename)
    shared = {column: files for column, files in column_files.items() if len(files) >= 2}
    report += ["## Shared columns", ""]
    shared_rows = []
    for column, files in sorted(shared.items()):
        dtypes = "; ".join(f"{filename}: {frames[filename][column].dtype}" for filename in files)
        shared_rows.append([column, dtypes])
    report += table(["Column", "Dtype by file"], shared_rows) if shared_rows else ["None."]
    report += ["", "## Shared id-like columns: child values absent from smallest file", ""]
    missing_rows = []
    for column, files in sorted(shared.items()):
        if not is_id_column(column):
            continue
        parent = min(files, key=lambda filename: len(frames[filename]))
        parent_values = id_values(frames[parent], column)
        for child in files:
            if child == parent:
                continue
            child_values = id_values(frames[child], column)
            missing_rows.append([column, child, parent, len(child_values - parent_values)])
    report += table(["Column", "Child file", "Comparison file", "Child ids missing"]) if not missing_rows else table(
        ["Column", "Child file", "Comparison file", "Child ids missing"], missing_rows)

    matches = frames.get("matches.csv")
    if matches is not None:
        report += ["", "## Matches per competition per season", ""]
        competition_col = find_column(matches, ("competition", "comp_"))
        season_col = find_column(matches, ("season",))
        date_col = find_column(matches, ("date", "start", "datetime"))
        if competition_col and season_col:
            grouped = matches.groupby([competition_col, season_col], dropna=False).size().reset_index(name="matches")
            rows = grouped.head(100).values.tolist()
            report += table([competition_col, season_col, "Matches"], rows)
        elif competition_col and date_col:
            dates = pd.to_datetime(matches[date_col], errors="coerce")
            grouped = matches.assign(_season=dates.dt.year).groupby([competition_col, "_season"], dropna=False).size().reset_index(name="matches")
            report += table([competition_col, "Derived year", "Matches"], grouped.head(100).values.tolist())
        else:
            report += ["Could not identify competition and season/date columns."]

    ball = frames.get("ball_by_ball.csv")
    report += ["", "## Match and result checks", ""]
    if ball is not None and matches is not None:
        ball_match = find_column(ball, ("match_id",)) or find_column(ball, ("match",))
        match_match = find_column(matches, ("match_id",)) or find_column(matches, ("match",))
        if ball_match and match_match:
            report += [f"- Ball-by-ball match ids: {ball[ball_match].nunique(dropna=True):,}; matches.csv match ids: {matches[match_match].nunique(dropna=True):,}"]
        else:
            report += ["Could not identify match id columns for the count comparison."]
    winner_file = matches if matches is not None else ball
    winner_col = None
    result_col = None
    if winner_file is not None:
        winner_col = find_exact_column(winner_file, ("win_team_id", "winner"))
        result_col = find_column(winner_file, ("result",))
    if winner_file is not None and (winner_col or result_col):
        winner = winner_file[winner_col] if winner_col else winner_file[result_col]
        result = winner_file[result_col] if result_col else winner
        text = result.fillna("").astype(str).str.strip()
        markers = {
            "winner = null": int(winner.isna().sum()),
            "tie": int(text.str.lower().eq("tie").sum()),
            "no result": int(text.str.lower().eq("no result").sum()),
            "D/L or revised target marker": int(text.str.contains(r"\bD/?L\b|revised\s+target|DLS|Duckworth", case=False, regex=True, na=False).sum()),
        }
        report += table(["Condition", "Count"], list(markers.items()))
        source = "matches.csv" if matches is not None else "ball_by_ball.csv"
        report += [f"Winner source: `{winner_col or '(not identified)'}`; result marker source: `{result_col or '(not identified)'}` in `{source}`."]
    else:
        report += ["No winner/result column identified."]

    report += ["", "## Ball-by-ball innings and over checks", ""]
    if ball is not None:
        innings_col = find_column(ball, ("innings",))
        over_col = find_column(ball, ("over",))
        ball_col = find_column(ball, ("ball",))
        rows = []
        if innings_col:
            counts = ball[innings_col].value_counts(dropna=False)
            rows.append(["Innings values", "; ".join(f"{md(k)} ({v})" for k, v in counts.items())])
            numeric_innings = pd.to_numeric(ball[innings_col], errors="coerce")
            rows.append(["Rows with innings > 2", int((numeric_innings > 2).sum())])
        if over_col:
            numeric_over = pd.to_numeric(ball[over_col], errors="coerce").dropna()
            if not numeric_over.empty:
                rows.append(["Over range", f"{numeric_over.min()} to {numeric_over.max()}"])
        if ball_col:
            numeric_ball = pd.to_numeric(ball[ball_col], errors="coerce").dropna()
            if not numeric_ball.empty:
                rows.append(["Ball-in-over range", f"{numeric_ball.min()} to {numeric_ball.max()}"])
        report += table(["Metric", "Value"], rows) if rows else ["Could not identify innings, over, or ball columns."]
    else:
        report += ["ball_by_ball.csv unavailable."]

    report += ["", "## Player names", ""]
    name_rows = []
    for filename, frame in frames.items():
        for column in frame.columns:
            if re.search(r"(?:^|_)(player|person).*name|name.*(?:player|person)", str(column), re.I):
                name_rows.append([filename, str(column)])
    report += table(["File", "Name column"], name_rows) if name_rows else ["No player name columns identified; available fields may be ids only."]

    report += ["", "## Team type and Pakistan team names", ""]
    team_type_rows = []
    pakistan_names: set[str] = set()
    for filename, frame in frames.items():
        for column in frame.columns:
            lowered = str(column).lower()
            if "type" in lowered and "team" in lowered:
                team_type_rows.append([filename, str(column)])
        for column in frame.columns:
            if "team" in str(column).lower() and ("name" in str(column).lower() or frame[column].dtype == "object"):
                pakistan_names.update(str(value) for value in frame[column].dropna()
                                      if "pakistan" in str(value).lower())
    report += table(["File", "Column indicating team type"], team_type_rows) if team_type_rows else ["No team type column identified."]
    report += ["Distinct team names containing `Pakistan`: " + (", ".join(sorted(pakistan_names)) if pakistan_names else "none") + "."]

    report += ["", "## Distinct team names (maximum 80)", ""]
    team_sources: dict[str, set[str]] = {}
    for filename, frame in frames.items():
        for column in frame.columns:
            lowered = str(column).lower()
            if "team" in lowered and "name" in lowered:
                for value in frame[column].dropna().unique():
                    team_sources.setdefault(str(value), set()).add(filename)
    team_rows = [[name, ", ".join(sorted(sources))] for name, sources in sorted(team_sources.items())[:80]]
    report += table(["Team name", "Source file(s)"], team_rows) if team_rows else ["No team-name columns identified."]

    report += ["", "## OPEN QUESTIONS", ""]
    questions = [
        "Cross-file parent selection for shared ids uses the smallest file containing that id column; confirm the intended relational parent if this heuristic is not correct.",
        "Date-like detection uses column names containing date, datetime, timestamp, or season, plus datetime dtypes; confirm any unlabeled date fields.",
        "Competition season grouping prefers a season column and otherwise derives calendar year from the first date-like match column.",
    ]
    report += [f"- {question}" for question in questions]
    report = [line for line in report if line.strip()]
    (ROOT / "schema_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(ROOT / "schema_report.md")


if __name__ == "__main__":
    main()
