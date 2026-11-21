"use strict";

const colors = [
  "#de6b45",
  "#487bb2",
  "#d1a42c",
  "#7d5ca6",
  "#3f997d",
  "#c04d79",
  "#607b39",
  "#77828a",
];
const suitSymbols = {
  hearts: ["♥", "red"],
  diamonds: ["♦", "red"],
  clubs: ["♣", "black"],
  spades: ["♠", "black"],
};
const landing = document.getElementById("landing");
const roomView = document.getElementById("room");
const lobbyView = document.getElementById("lobby");
const gameView = document.getElementById("game");
const errorView = document.getElementById("error");
const connectionView = document.getElementById("connection");
let gameState = null;
let roomCode = "";
let playerToken = "";
let hostToken = "";
let socket = null;
let reconnectTimer = null;
let selectedCardId = "";
let inviteUrl = "";

function playerTokenKey(code) {
  return `keez:${code}:player`;
}

function hostTokenKey(code) {
  return `keez:${code}:host`;
}

function showError(message) {
  errorView.textContent = message;
  errorView.hidden = !message;
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (playerToken) headers.set("X-Player-Token", playerToken);
  if (hostToken) headers.set("X-Host-Token", hostToken);
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json();
  if (!response.ok) {
    const detail = payload.detail || `Request failed (${response.status}).`;
    const error = new Error(
      Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail,
    );
    error.status = response.status;
    throw error;
  }
  return payload;
}

function saveRoomCredentials(code, player, host) {
  roomCode = code;
  playerToken = player;
  hostToken = host || "";
  localStorage.setItem("keez:active-room", code);
  localStorage.setItem(playerTokenKey(code), player);
  if (host) localStorage.setItem(hostTokenKey(code), host);
}

async function openRoom(code, token) {
  const normalized = code.trim().toUpperCase();
  if (!normalized) throw new Error("Enter a room code.");
  const result = await request(`/api/rooms/${encodeURIComponent(normalized)}/state`, {
    headers: { "X-Player-Token": token },
  });
  gameState = result;
  roomCode = normalized;
  playerToken = token;
  hostToken = localStorage.getItem(hostTokenKey(normalized)) || "";
  inviteUrl = result.invite_url || localStorage.getItem(`keez:${normalized}:invite`) || "";
  if (inviteUrl) localStorage.setItem(`keez:${normalized}:invite`, inviteUrl);
  landing.hidden = true;
  roomView.hidden = false;
  render();
  connect();
}

function connect() {
  if (!roomCode || !playerToken) return;
  if (socket) {
    const previous = socket;
    socket = null;
    previous.close();
  }
  if (reconnectTimer) clearTimeout(reconnectTimer);
  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  socket = new WebSocket(
    `${scheme}//${location.host}/ws/${encodeURIComponent(roomCode)}`,
  );
  const activeSocket = socket;
  activeSocket.onopen = () => {
    activeSocket.send(playerToken);
    connectionView.textContent = "Connected";
    connectionView.classList.add("online");
  };
  activeSocket.onmessage = (event) => {
    gameState = JSON.parse(event.data);
    render();
  };
  activeSocket.onclose = () => {
    if (socket !== activeSocket) return;
    connectionView.textContent = "Reconnecting…";
    connectionView.classList.remove("online");
    reconnectTimer = setTimeout(connect, 1600);
  };
  activeSocket.onerror = () => activeSocket.close();
}

function render() {
  if (!gameState) return;
  landing.hidden = true;
  roomView.hidden = false;
  document.getElementById("room-code").textContent = gameState.code;
  const invite = document.getElementById("invite");
  const sharedUrl = inviteUrl || `${location.origin}/?room=${gameState.code}`;
  invite.href = sharedUrl;
  invite.textContent = sharedUrl;
  invite.title = "Share this LAN link with players";

  const isLobby = gameState.status === "lobby";
  lobbyView.hidden = !isLobby;
  gameView.hidden = isLobby;
  if (isLobby) {
    renderLobby();
    return;
  }
  renderGame();
}

function renderLobby() {
  const players = gameState.players;
  document.getElementById("layout-description").textContent =
    `${players.length} of 8 seats filled. ${gameState.layout || "Board layout is selected when the game starts."}`;
  const list = document.getElementById("seat-list");
  list.replaceChildren();
  players.forEach((player, index) => {
    const item = document.createElement("li");
    const partner = player.partner_id
      ? players.find((candidate) => candidate.id === player.partner_id)
      : null;
    item.append(document.createTextNode(`${player.name}${player.id === gameState.host_player_id ? " (host)" : ""}`));
    if (partner) {
      const partnerLabel = document.createElement("span");
      partnerLabel.className = "muted";
      partnerLabel.textContent = ` — partner: ${partner.name}`;
      item.append(partnerLabel);
    }
    if (gameState.host) {
      const tools = document.createElement("span");
      tools.className = "seat-tools";
      for (const [label, delta] of [["↑", -1], ["↓", 1]]) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = label;
        button.setAttribute("aria-label", `${label === "↑" ? "Move up" : "Move down"} ${player.name}`);
        button.disabled = index + delta < 0 || index + delta >= players.length;
        button.addEventListener("click", () => moveSeat(index, delta));
        tools.append(button);
      }
      item.append(tools);
    }
    list.append(item);
  });
  const start = document.getElementById("start-button");
  start.hidden = !gameState.host;
  start.disabled = players.length < 3 || players.length > 8;
  document.getElementById("lobby-help").textContent = gameState.host
    ? "As host, you occupy a seat. Reorder seats before starting; opposite seats are partners in even-player games."
    : "Use the room invite on your own browser to claim a seat. The host can reorder seats and start once at least three players have joined.";
}

async function moveSeat(index, delta) {
  const ids = gameState.players.map((player) => player.id);
  const target = index + delta;
  [ids[index], ids[target]] = [ids[target], ids[index]];
  try {
    gameState = await request(`/api/rooms/${roomCode}/seats`, {
      method: "PUT",
      body: JSON.stringify({ player_ids: ids }),
    });
    render();
  } catch (error) {
    showError(error.message);
  }
}

function renderGame() {
  const current = gameState.players.find((player) => player.id === gameState.current_player_id);
  const ownPlayer = gameState.players.find((player) => player.is_you);
  const turnStatus = document.getElementById("turn-status");
  if (gameState.status === "finished") {
    const winners = gameState.players
      .filter((player) => gameState.winner_player_ids.includes(player.id))
      .map((player) => player.name);
    turnStatus.textContent = `Game over — ${winners.join(" and ")} won!`;
  } else if (gameState.status === "stalled") {
    turnStatus.textContent = "The game is stalled: no legal moves remain.";
  } else if (gameState.waiting_for_reconnect && current) {
    turnStatus.textContent = `Waiting for ${current.name} to reconnect.`;
  } else if (current && current.is_you) {
    turnStatus.textContent = "Your turn";
  } else if (current) {
    turnStatus.textContent = `${current.name}'s turn`;
  } else {
    turnStatus.textContent = "Game in progress";
  }
  document.getElementById("deal-status").textContent =
    gameState.status === "playing"
      ? `Deal ${gameState.deal_number} · ${gameState.hand_size} cards · ${gameState.layout} · ${gameState.track_length} track spaces`
      : `${gameState.layout} · ${gameState.track_length} track spaces per lap`;
  renderBoard();
  renderLegend();
  renderHand(ownPlayer);
  renderNotices();
  document.getElementById("new-room-button").hidden =
    !gameState.host || !["finished", "stalled"].includes(gameState.status);
}

function renderHand(player) {
  const hand = document.getElementById("hand");
  hand.replaceChildren();
  const cards = player ? player.hand || [] : [];
  const isTurn = player && player.id === gameState.current_player_id && gameState.status === "playing";
  cards.forEach((card) => {
    const [symbol, color] = suitSymbols[card.suit];
    const button = document.createElement("button");
    button.type = "button";
    button.className = `card ${color}${card.id === selectedCardId ? " selected" : ""}`;
    button.textContent = `${card.rank}${symbol}`;
    button.disabled = !isTurn;
    button.title = `${card.rank} of ${card.suit}`;
    button.addEventListener("click", () => {
      selectedCardId = selectedCardId === card.id ? "" : card.id;
      renderHand(player);
    });
    hand.append(button);
  });

  const actions = document.getElementById("action-list");
  actions.replaceChildren();
  if (!isTurn) {
    actions.append(messageNode(cards.length ? "Your cards are private; wait for your turn." : "No cards in hand."));
    return;
  }
  const available = gameState.legal_actions.filter((action) => action.card_id === selectedCardId);
  if (!selectedCardId) {
    actions.append(messageNode("Select a card to see its legal moves."));
    return;
  }
  if (!available.length) {
    actions.append(messageNode("That card has no legal move. Select another card."));
    return;
  }
  available.forEach((action) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = describeAction(action);
    button.addEventListener("click", () => submitAction(action));
    actions.append(button);
  });
}

function describeAction(action) {
  const owners = new Map(gameState.players.map((player) => [player.id, player.name]));
  if (action.type === "setup") {
    const move = action.moves[0];
    return `Place ${owners.get(move.player_id)} pawn ${move.pawn + 1} on its start`;
  }
  if (action.type === "swap") {
    const move = action.moves[0];
    return `Swap ${owners.get(move.player_id)} pawn ${move.pawn + 1} with ${owners.get(move.target_player_id)} pawn ${move.target_pawn + 1}`;
  }
  if (action.type === "split") {
    return `Split Seven: ${action.moves.map((move) => `${owners.get(move.player_id)} pawn ${move.pawn + 1} by ${move.steps}`).join(" + ")}`;
  }
  const move = action.moves[0];
  return `Move ${owners.get(move.player_id)} pawn ${move.pawn + 1} by ${Math.abs(move.steps)}${move.steps < 0 ? " backward" : ""}`;
}

function messageNode(text) {
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  return paragraph;
}

async function submitAction(action) {
  showError("");
  try {
    const result = await request(`/api/rooms/${roomCode}/move`, {
      method: "POST",
      body: JSON.stringify({ action }),
    });
    gameState = result;
    selectedCardId = "";
    render();
  } catch (error) {
    showError(error.message);
  }
}

function renderNotices() {
  const list = document.getElementById("notices");
  list.replaceChildren();
  for (const notice of [...gameState.notices].reverse()) {
    const item = document.createElement("li");
    item.textContent = notice;
    list.append(item);
  }
}

function renderLegend() {
  const legend = document.getElementById("player-legend");
  legend.replaceChildren();
  gameState.players.forEach((player, index) => {
    const item = document.createElement("span");
    item.className = "legend-item";
    const dot = document.createElement("span");
    dot.className = "legend-dot";
    dot.style.backgroundColor = colors[index % colors.length];
    const pieceType = gameState.piece_types[player.seat];
    const pieceLabel = pieceType === "custom" ? "custom" : `${pieceType}° piece`;
    item.append(
      dot,
      document.createTextNode(`Seat ${player.seat + 1}: ${player.name} (${pieceLabel})`),
    );
    legend.append(item);
  });
}

function renderBoard() {
  const svg = document.getElementById("board");
  svg.replaceChildren();
  const playerCount = gameState.players.length;
  const trackLength = gameState.track_length;
  const bySeat = [...gameState.players].sort((a, b) => a.seat - b.seat);
  const coordinates = [];
  const radius = 350;
  const seatGeometry = [];
  const totalPieceWeight = gameState.piece_types.reduce(
    (total, pieceType) => total + (pieceType === "180" ? 2 : 1),
    0,
  );
  let cumulativePieceWeight = 0;
  for (const player of bySeat) {
    const pieceType = gameState.piece_types[player.seat];
    const weight = pieceType === "180" ? 2 : 1;
    seatGeometry[player.seat] = {
      start: -Math.PI / 2 + Math.PI * 2 * cumulativePieceWeight / totalPieceWeight,
      span: Math.PI * 2 * weight / totalPieceWeight,
    };
    cumulativePieceWeight += weight;
  }
  const smallestTrackStep = Math.min(
    ...seatGeometry.map(({ span }) => span / 16),
  );
  for (let index = 0; index < trackLength; index += 1) {
    const seat = Math.floor(index / 16) % playerCount;
    const positionInSeat = index % 16;
    const angle = seatGeometry[seat].start + seatGeometry[seat].span * positionInSeat / 16;
    coordinates.push([400 + Math.cos(angle) * radius, 400 + Math.sin(angle) * radius]);
  }
  const path = svgElement("polyline", {
    points: [...coordinates, coordinates[0]].map(([x, y]) => `${x},${y}`).join(" "),
    fill: "none",
    stroke: "#9eacb3",
    "stroke-width": 3,
    "stroke-linejoin": "round",
  });
  svg.append(path);
  const cellRadius = Math.min(12, Math.max(4, radius * smallestTrackStep * 0.43));
  const pawnRadius = Math.min(8, cellRadius * 0.82);

  for (let global = 0; global < trackLength; global += 1) {
    const [x, y] = coordinates[global];
    const owner = bySeat[Math.floor(global / 16) % playerCount];
    const circle = svgElement("circle", {
      cx: x,
      cy: y,
      r: cellRadius,
      fill: tint(colors[owner.seat % colors.length]),
      stroke: colors[owner.seat % colors.length],
      class: global % 16 === 0 ? "track-cell start-cell" : "track-cell",
    });
    svg.append(circle);
    const label = svgElement("text", { x, y, class: "cell-label" });
    label.textContent = `${owner.seat + 1}`;
    svg.append(label);
  }

  for (const player of bySeat) {
    const color = colors[player.seat % colors.length];
    const startGlobal = (player.seat * 16) % trackLength;
    const [startX, startY] = coordinates[startGlobal];
    const vectorLength = Math.hypot(400 - startX, 400 - startY) || 1;
    const inwardX = (400 - startX) / vectorLength;
    const inwardY = (400 - startY) / vectorLength;
    const { start, span } = seatGeometry[player.seat];
    const angle = start + span / 2;
    const waitCenterX = 400 + Math.cos(angle) * 145;
    const waitCenterY = 400 + Math.sin(angle) * 145;
    const homePositions = [];
    const waitingPositions = [];
    for (let pawn = 0; pawn < 4; pawn += 1) {
      homePositions.push([
        startX + inwardX * (31 + pawn * 27),
        startY + inwardY * (31 + pawn * 27),
      ]);
      waitingPositions.push([
        waitCenterX + (pawn % 2 === 0 ? -1 : 1) * 12,
        waitCenterY + (pawn < 2 ? -1 : 1) * 12,
      ]);
    }
    for (const [x, y] of homePositions) {
      svg.append(svgElement("circle", {
        cx: x,
        cy: y,
        r: 12,
        fill: tint(color),
        stroke: color,
        class: "home-cell",
      }));
    }
    for (const [x, y] of waitingPositions) {
      svg.append(svgElement("circle", {
        cx: x,
        cy: y,
        r: 12,
        fill: "#fff",
        stroke: color,
        class: "waiting-cell",
      }));
    }
    for (let pawn = 0; pawn < 4; pawn += 1) {
      const position = player.pawns[pawn];
      let x;
      let y;
      if (position === -1) {
        [x, y] = waitingPositions[pawn];
      } else if (position < trackLength) {
        const global = (player.seat * 16 + position) % trackLength;
        [x, y] = coordinates[global];
      } else {
        const homeIndex = position - trackLength;
        [x, y] = homePositions[homeIndex];
      }
      svg.append(svgElement("circle", {
        cx: x,
        cy: y,
        r: pawnRadius,
        fill: color,
        class: "pawn-token",
      }));
      const number = svgElement("text", {
        x,
        y: y + 0.5,
        fill: "#fff",
        "font-size": Math.max(5, pawnRadius * 1.1),
        "font-weight": 700,
        "text-anchor": "middle",
        "dominant-baseline": "central",
      });
      number.textContent = `${pawn + 1}`;
      svg.append(number);
    }
  }

  const title = svgElement("text", { x: 400, y: 390, class: "board-title" });
  title.textContent = "KEEZ";
  svg.append(title);
  const subtitle = svgElement("text", {
    x: 400,
    y: 420,
    fill: "#596a75",
    "font-size": 13,
    "text-anchor": "middle",
  });
  subtitle.textContent = `${playerCount} players · ${gameState.layout}`;
  svg.append(subtitle);
}

function svgElement(name, attributes) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  return element;
}

function tint(hex) {
  const value = Number.parseInt(hex.slice(1), 16);
  const red = Math.round(((value >> 16) & 255) * 0.28 + 255 * 0.72);
  const green = Math.round(((value >> 8) & 255) * 0.28 + 255 * 0.72);
  const blue = Math.round((value & 255) * 0.28 + 255 * 0.72);
  return `rgb(${red}, ${green}, ${blue})`;
}

document.getElementById("create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  const form = new FormData(event.currentTarget);
  try {
    const result = await request("/api/rooms", {
      method: "POST",
      body: JSON.stringify({ display_name: form.get("display_name") }),
    });
    saveRoomCredentials(result.state.code, result.player_token, result.host_token);
    gameState = result.state;
    inviteUrl = result.invite_url;
    localStorage.setItem(`keez:${gameState.code}:invite`, inviteUrl);
    history.replaceState(null, "", `/?room=${gameState.code}`);
    render();
    connect();
  } catch (error) {
    showError(error.message);
  }
});

document.getElementById("join-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  showError("");
  const form = new FormData(event.currentTarget);
  const code = String(form.get("code")).trim().toUpperCase();
  const previousToken = localStorage.getItem(playerTokenKey(code)) || "";
  try {
    const result = await request(`/api/rooms/${encodeURIComponent(code)}/join`, {
      method: "POST",
      body: JSON.stringify({
        display_name: form.get("display_name"),
        player_token: previousToken || null,
      }),
    });
    saveRoomCredentials(code, result.player_token, localStorage.getItem(hostTokenKey(code)) || "");
    gameState = result.state;
    inviteUrl = result.invite_url || "";
    if (inviteUrl) localStorage.setItem(`keez:${code}:invite`, inviteUrl);
    history.replaceState(null, "", `/?room=${gameState.code}`);
    render();
    connect();
  } catch (error) {
    showError(error.message);
  }
});

document.getElementById("start-button").addEventListener("click", async () => {
  showError("");
  try {
    gameState = await request(`/api/rooms/${roomCode}/start`, { method: "POST" });
    render();
  } catch (error) {
    showError(error.message);
  }
});

document.getElementById("new-room-button").addEventListener("click", () => {
  if (socket) {
    const previous = socket;
    socket = null;
    previous.close();
  }
  localStorage.removeItem("keez:active-room");
  gameState = null;
  roomCode = "";
  playerToken = "";
  hostToken = "";
  inviteUrl = "";
  roomView.hidden = true;
  landing.hidden = false;
  history.replaceState(null, "", "/");
});

async function boot() {
  document.getElementById("join-form").elements.code.value =
    new URLSearchParams(location.search).get("room") || "";
  const code = new URLSearchParams(location.search).get("room")
    || localStorage.getItem("keez:active-room");
  if (!code) return;
  const token = localStorage.getItem(playerTokenKey(code.toUpperCase()));
  if (!token) return;
  try {
    await openRoom(code, token);
  } catch (error) {
    if (error.status === 401 || error.status === 404) {
      localStorage.removeItem(playerTokenKey(code.toUpperCase()));
    }
    showError(`Unable to reopen room: ${error.message}`);
  }
}

boot();
