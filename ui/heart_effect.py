"""Pixel-heart keyframes shared by the Qt painter and the review preview."""
HEART_MASK = ('0110110', '1111111', '1111111', '0111110', '0011100', '0001000')
DURATION = .95
WIDTH, HEIGHT = 80, 56


def hearts_at(elapsed):
    if elapsed < 0 or elapsed >= DURATION:
        return []
    hearts = []
    for x, scale, delay in ((12, 1, 0), (32, 2, .1), (60, 1, .2)):
        age = elapsed - delay
        if 0 <= age < .75:
            alpha = round(255 * max(0, min(1, age / .08, (.75 - age) / .32)))
            hearts.append((x, 40 - round(20 * age / .75), scale, alpha))
    return hearts
