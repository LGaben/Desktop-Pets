"""The supported pets, in display order (no Qt objects at import time)."""

PET_EMOJI = dict(zip(
    ("fox", "panda", "cockatiel", "dog", "turtle", "totoro", "chicken",
     "clippy", "crab", "deno", "horse", "mod", "monkey", "morph", "rat",
     "rocky", "rubber_duck", "skeleton", "snail", "snake", "zappy"),
    ("🦊", "🐼", "🐦", "🐕", "🐢", "🐻", "🐔", "📎", "🦀", "🦕", "🐴",
     "🔮", "🐒", "💜", "🐀", "🪨", "🦆", "💀", "🐌", "🐍", "⚡"),
))
PET_TYPES = tuple(PET_EMOJI)
