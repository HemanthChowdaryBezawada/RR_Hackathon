const files = ["meta", "players_batters", "players_bowlers", "pressure", "validation"];

export async function loadData() {
  const entries = await Promise.all(
    files.map(async (name) => {
      const response = await fetch(`data/${name}.json`);
      if (!response.ok) throw new Error(`${name}.json (${response.status})`);
      return [name, await response.json()];
    })
  );
  return Object.fromEntries(entries);
}

export function activePlayers(data, role) {
  if (!data) return [];
  const rows = role === "batter" ? data.players_batters : data.players_bowlers;
  return rows || [];
}

export function byId(data, id) {
  if (!data) return null;
  const all = [...(data.players_batters || []), ...(data.players_bowlers || [])];
  return all.find((p) => String(p.player_id) === String(id)) || null;
}
